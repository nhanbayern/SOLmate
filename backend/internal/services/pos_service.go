package services

import (
	"backend/internal/config"
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"fmt"
	"log/slog"
	"time"
)

type POSPostgresRepo interface {
	InsertTransactionLog(ctx context.Context, log *models.TransactionLog) error
	GetMerchantMetadata(ctx context.Context, id string) (*models.Merchant, error)
	GetTransactionHistory(ctx context.Context, merchantID, customerID string, since time.Time) ([]*models.TransactionLog, error)
}

type POSRedisRepo interface {
	UpdateFeatures(ctx context.Context, features *models.MerchantFeatures) error
	PublishUpdate(ctx context.Context, merchantID string, message string) error
}

type POSFeatureService interface {
	CalculateFeatures(ctx context.Context, merchant *models.Merchant, txns []*models.TransactionLog) ([]float64, error)
}

type POSService struct {
	pgRepo         POSPostgresRepo
	redisRepo      POSRedisRepo
	featureService POSFeatureService
	cfg            config.POSServiceConfig
	log            *slog.Logger
}

func NewPOSService(
	pgRepo POSPostgresRepo,
	redisRepo POSRedisRepo,
	featureService POSFeatureService,
	cfg config.POSServiceConfig,
) *POSService {
	logger := infrastructure.GetLogger("POS_Service")

	return &POSService{
		pgRepo:         pgRepo,
		redisRepo:      redisRepo,
		featureService: featureService,
		cfg:            cfg,
		log:            logger,
	}
}

func (s *POSService) publishError(ctx context.Context, merchantID, customerID string, reason string) {
	errMsg := fmt.Sprintf(
		`{"type": "ERROR", "merchant_id": "%s", "customer_id": "%s", "reason": "%s", "timestamp": "%s"}`,
		merchantID, customerID, reason, time.Now().Format(time.RFC3339),
	)

	if err := s.redisRepo.PublishUpdate(ctx, merchantID, errMsg); err != nil {
		s.log.Warn(
			"Publish Error SSE update failed",
			"merchant_id", merchantID,
			"customer_id", customerID,
			infrastructure.KeyError, err.Error(),
		)
	}
}

func (s *POSService) ProcessTransaction(ctx context.Context, log *models.TransactionLog) error {
	s.log.Debug(
		"Transaction processing",
		"id", log.ID,
		"merchant_id", log.MerchantID,
		"customer_id", log.CustomerID,
		"amount", log.Amount,
		"is_refund", log.IsRefund,
		"pos_terminal_id", log.POSTerminalID,
	)

	dbCtx, dbCancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer dbCancel()

	if err := s.pgRepo.InsertTransactionLog(dbCtx, log); err != nil {
		return fmt.Errorf("insert transaction log: %w", err)
	}

	go func() {
		calcCtx, cancel := context.WithTimeout(context.Background(), s.cfg.DBTimeout*3)
		defer cancel()

		merchant, err := s.pgRepo.GetMerchantMetadata(calcCtx, log.MerchantID)
		if err != nil {
			s.log.Error(
				"Fetch merchant metadata failed",
				"merchant_id", log.MerchantID,
				infrastructure.KeyError, err.Error(),
			)

			s.publishError(calcCtx, log.MerchantID, log.CustomerID, "Fetch merchant metadata failed")
			return
		}

		since := time.Now().AddDate(0, 0, -180)
		txns, err := s.pgRepo.GetTransactionHistory(calcCtx, log.MerchantID, log.CustomerID, since)
		if err != nil {
			s.log.Error(
				"Fetch transaction history failed",
				"merchant_id", log.MerchantID,
				"customer_id", log.CustomerID,
				infrastructure.KeyError, err.Error(),
			)

			s.publishError(calcCtx, log.MerchantID, log.CustomerID, "Fetch transaction history failed")
			return
		}

		featuresArr, err := s.featureService.CalculateFeatures(calcCtx, merchant, txns)
		if err != nil {
			s.log.Error(
				"Feature calculation failed",
				"merchant_id", log.MerchantID,
				"customer_id", log.CustomerID,
				infrastructure.KeyError, err.Error(),
			)

			s.publishError(calcCtx, log.MerchantID, log.CustomerID, "Feature calculation failed")
			return
		}

		features := &models.MerchantFeatures{
			MerchantID: log.MerchantID,
			CustomerID: log.CustomerID,
			Features:   featuresArr,
		}

		if err := s.redisRepo.UpdateFeatures(calcCtx, features); err != nil {
			s.log.Error(
				"Save features to Redis failed",
				"merchant_id", log.MerchantID,
				"customer_id", log.CustomerID,
				infrastructure.KeyError, err.Error(),
			)

			s.publishError(calcCtx, log.MerchantID, log.CustomerID, "Update internal cache failed")
			return
		}

		updateMsg := fmt.Sprintf(
			`{"type": "FEATURES_UPDATED", "merchant_id": "%s", "customer_id": "%s", "timestamp": "%s"}`,
			log.MerchantID, log.CustomerID, time.Now().Format(time.RFC3339),
		)

		if err := s.redisRepo.PublishUpdate(calcCtx, log.MerchantID, updateMsg); err != nil {
			s.log.Warn(
				"Publish SSE update failed",
				"merchant_id", log.MerchantID,
				"customer_id", log.CustomerID,
				infrastructure.KeyError, err.Error(),
			)
		}
	}()

	return nil
}
