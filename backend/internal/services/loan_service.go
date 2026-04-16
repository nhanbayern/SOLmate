package services

import (
	"backend/internal/config"
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"errors"
	"fmt"
	"log/slog"
	"math"
	"sync"
	"time"

	ort "github.com/yalue/onnxruntime_go"
)

type LoanPostgresRepo interface {
	UpdateLoanAIReport(ctx context.Context, loanID, score int, riskLabel string, pdValue float64, report string) error
}

type LoanRedisRepo interface {
	GetFeatures(ctx context.Context, merchantID, customerID string) (*models.MerchantFeatures, error)
	PublishUpdate(ctx context.Context, merchantID string, message string) error
}

type LoanAgentService interface {
	ReviewRisk(ctx context.Context, reqData models.AgentRiskRequest) (*models.AgentRiskResponse, error)
}

type LoanService struct {
	pgRepo       LoanPostgresRepo
	redisRepo    LoanRedisRepo
	agentService LoanAgentService
	session      *ort.AdvancedSession
	inputTensor  *ort.Tensor[float32]
	outputTensor *ort.Tensor[float32]
	mu           sync.Mutex
	cfg          config.LoanServiceConfig
	log          *slog.Logger
}

func NewLoanService(
	pgRepo LoanPostgresRepo,
	redisRepo LoanRedisRepo,
	agentService LoanAgentService,
	cfg config.LoanServiceConfig,
	dllPath, modelPath string,
) (*LoanService, error) {
	logger := infrastructure.GetLogger("LOAN_SERVICE")

	ort.SetSharedLibraryPath(dllPath)
	if !ort.IsInitialized() {
		if err := ort.InitializeEnvironment(); err != nil {
			return nil, fmt.Errorf("init onnx environment: %w", err)
		}
	}

	inputShape := ort.NewShape(1, int64(cfg.FeatureCount))
	inputTensor, err := ort.NewEmptyTensor[float32](inputShape)
	if err != nil {
		return nil, fmt.Errorf("create input tensor: %w", err)
	}

	outputShape := ort.NewShape(1, int64(cfg.OutputClass))
	outputTensor, err := ort.NewEmptyTensor[float32](outputShape)
	if err != nil {
		return nil, fmt.Errorf("create output tensor: %w", err)
	}

	session, err := ort.NewAdvancedSession(
		modelPath,
		[]string{cfg.ModelInputName},
		[]string{cfg.ModelOutputName},
		[]ort.Value{inputTensor},
		[]ort.Value{outputTensor},
		nil,
	)
	if err != nil {
		return nil, fmt.Errorf("create advanced session: %w", err)
	}

	logger.Info(
		"Model loaded successfully",
		"model", modelPath,
	)

	return &LoanService{
		pgRepo:       pgRepo,
		redisRepo:    redisRepo,
		agentService: agentService,
		cfg:          cfg,
		log:          logger,
		session:      session,
		inputTensor:  inputTensor,
		outputTensor: outputTensor,
	}, nil
}

func (s *LoanService) publishError(ctx context.Context, merchantID, customerID string, reason string) {
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

func (s *LoanService) EvaluateLoan(ctx context.Context, loanID int, merchantID, customerID string) error {
	s.log.Debug(
		"Loan evaluation started",
		"loan_id", loanID,
		"merchant_id", merchantID,
		"customer_id", customerID,
	)

	redisCtx, cancel := context.WithTimeout(ctx, s.cfg.RedisTimeout)
	defer cancel()

	merchantData, err := s.redisRepo.GetFeatures(redisCtx, merchantID, customerID)
	if err != nil {
		s.log.Error(
			"Get features failed",
			"loan_id", loanID,
			"customer_id", customerID,
			infrastructure.KeyError, err.Error(),
		)

		s.publishError(ctx, merchantID, customerID, "No transaction features found in cache")

		return fmt.Errorf("get features: %w", err)
	}

	if len(merchantData.Features) < s.cfg.FeatureCount {
		err := fmt.Errorf("expected %d, got %d", s.cfg.FeatureCount, len(merchantData.Features))
		s.log.Error(
			"Feature validation failed",
			"loan_id", loanID,
			"customer_id", customerID,
			infrastructure.KeyError, err.Error(),
		)

		s.publishError(ctx, merchantID, customerID, "Feature validation failed")

		return fmt.Errorf("validate features: %w", err)
	}

	modelFeatures := make([]float32, s.cfg.FeatureCount)
	for i := 0; i < s.cfg.FeatureCount; i++ {
		modelFeatures[i] = float32(merchantData.Features[i])
	}

	s.mu.Lock()
	inputData := s.inputTensor.GetData()
	copy(inputData, modelFeatures)

	if err := s.session.Run(); err != nil {
		s.mu.Unlock()

		s.log.Error(
			"Run model failed",
			"loan_id", loanID,
			infrastructure.KeyError, err.Error(),
		)

		s.publishError(ctx, merchantID, customerID, "Machine Learning model execution failed")

		return fmt.Errorf("run model: %w", err)
	}

	outputData := s.outputTensor.GetData()
	rawOutput := float64(outputData[s.cfg.PDIndex])
	s.mu.Unlock()

	pdValue := 1.0 / (1.0 + math.Exp(-rawOutput))

	score := int((1.0 - pdValue) * float64(s.cfg.MaxScore))
	var riskLabel string

	switch {
	case pdValue < s.cfg.VeryHighThreshold:
		riskLabel = "VERY_HIGH"
	case pdValue < s.cfg.HighThreshold:
		riskLabel = "HIGH"
	case pdValue < s.cfg.MediumThreshold:
		riskLabel = "MEDIUM"
	case pdValue < s.cfg.LowThreshold:
		riskLabel = "LOW"
	default:
		riskLabel = "VERY_LOW"
	}

	s.log.Info(
		"Model evaluated successfully",
		"loan_id", loanID,
		"merchant_id", merchantID,
		"customer_id", customerID,
		"score", score,
		"risk_label", riskLabel,
		"pd_value", fmt.Sprintf("%.4f", pdValue),
	)

	agentReq := models.AgentRiskRequest{
		CustomerID:      customerID,
		CreditScore:     float64(score),
		RiskClass:       riskLabel,
		RiskProbability: pdValue,
	}

	f := merchantData.Features

	if len(f) >= 12 {
		agentReq.Metrics = models.AgentMetrics{
			RevenueMean30d: f[0],
			RevenueMean90d: f[1],
			TxnFrequency:   f[2],
			GrowthValue:    f[3],
			GrowthScore:    f[4],
			CVValue:        f[5],
			CVScore:        f[6],
			SpikeRatio:     f[7],
			SpikeScore:     f[8],
			TxnFreqScore:   f[9],
			YearsScore:     f[10],
			IndustryScore:  f[11],
			Regime:         riskLabel,
		}
	} else if len(f) >= 6 {
		agentReq.Metrics = models.AgentMetrics{
			RevenueMean30d: f[0],
			RevenueMean90d: f[1],
			TxnFrequency:   f[2],
			GrowthValue:    f[3],
			CVValue:        f[4],
			SpikeRatio:     f[5],
			Regime:         riskLabel,
		}
	}

	var reportText string
	agentRes, err := s.agentService.ReviewRisk(ctx, agentReq)
	if err != nil {
		s.log.Warn(
			"Agent review failed",
			"loan_id", loanID,
			"merchant_id", merchantID,
			"customer_id", customerID,
			"score", score,
			"risk_label", riskLabel,
			"pd_value", fmt.Sprintf("%.4f", pdValue),
			infrastructure.KeyError, err.Error(),
		)

		reportText = "AI Agent hiện không khả dụng để phân tích báo cáo chi tiết."
	} else {
		reportText = agentRes.ReportText
	}

	dbCtx, dbCancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer dbCancel()

	if err := s.pgRepo.UpdateLoanAIReport(dbCtx, loanID, score, riskLabel, pdValue, reportText); err != nil {
		s.log.Error(
			"Update database failed",
			"loan_id", loanID,
			"customer_id", customerID,
			infrastructure.KeyError, err.Error(),
		)

		s.publishError(ctx, merchantID, customerID, "Save evaluation result failed")

		return fmt.Errorf("update db: %w", err)
	}

	sseMsg := fmt.Sprintf(
		`{"type": "EVALUATION_COMPLETED", "loan_id": %d, "merchant_id": "%s", "customer_id": "%s", "score": %d, "risk_label": "%s", "pd_value": %.4f}`,
		loanID, merchantID, customerID, score, riskLabel, pdValue,
	)

	if err := s.redisRepo.PublishUpdate(ctx, merchantID, sseMsg); err != nil {
		s.log.Warn(
			"Publish SSE update failed",
			"merchant_id", merchantID,
			"customer_id", customerID,
			infrastructure.KeyError, err.Error(),
		)
	}

	return nil
}

func (s *LoanService) Close() error {
	var errs []error

	if s.session != nil {
		if err := s.session.Destroy(); err != nil {
			errs = append(errs, fmt.Errorf("destroy session: %w", err))
		}
	}

	if s.inputTensor != nil {
		if err := s.inputTensor.Destroy(); err != nil {
			errs = append(errs, fmt.Errorf("destroy input tensor: %w", err))
		}
	}

	if s.outputTensor != nil {
		if err := s.outputTensor.Destroy(); err != nil {
			errs = append(errs, fmt.Errorf("destroy output tensor: %w", err))
		}
	}

	if len(errs) > 0 {
		finalErr := errors.Join(errs...)

		s.log.Error(
			"Close AI session failed",
			infrastructure.KeyError, finalErr.Error(),
		)

		return finalErr
	}

	s.log.Info("AI session closed successfully")

	return nil
}
