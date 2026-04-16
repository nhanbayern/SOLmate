package services

import (
	"backend/internal/config"
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"log/slog"
	"time"
)

type DashboardPostgresRepo interface {
	GetMerchantMetadata(ctx context.Context, id string) (*models.Merchant, error)
	GetTransactionHistory(ctx context.Context, merchantID, customerID string, since time.Time) ([]*models.TransactionLog, error)
	GetAllMerchants(ctx context.Context) ([]*models.Merchant, error)
	GetAllLoanRequests(ctx context.Context) ([]*models.LoanRequest, error)
	GetLoanRequestByID(ctx context.Context, id int) (*models.LoanRequest, error)
	GetDashboardStats(ctx context.Context) (*models.DashboardStats, error)
}

type DashboardService struct {
	pgRepo DashboardPostgresRepo
	cfg    config.LoanServiceConfig
	log    *slog.Logger
}

func NewDashboardService(pgRepo DashboardPostgresRepo, cfg config.LoanServiceConfig) *DashboardService {
	logger := infrastructure.GetLogger("DASHBOARD_SERVICE")

	return &DashboardService{
		pgRepo: pgRepo,
		cfg:    cfg,
		log:    logger,
	}
}

func (s *DashboardService) ListMerchants(ctx context.Context) ([]*models.Merchant, error) {
	dbCtx, cancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer cancel()

	return s.pgRepo.GetAllMerchants(dbCtx)
}

func (s *DashboardService) GetMerchant(ctx context.Context, id string) (*models.Merchant, error) {
	dbCtx, cancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer cancel()

	return s.pgRepo.GetMerchantMetadata(dbCtx, id)
}

func (s *DashboardService) ListLoanRequests(ctx context.Context) ([]*models.LoanRequest, error) {
	dbCtx, cancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer cancel()

	return s.pgRepo.GetAllLoanRequests(dbCtx)
}

func (s *DashboardService) GetLoanRequest(ctx context.Context, id int) (*models.LoanRequest, error) {
	dbCtx, cancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer cancel()

	return s.pgRepo.GetLoanRequestByID(dbCtx, id)
}

func (s *DashboardService) GetTransactions(ctx context.Context, merchantID, customerID string) ([]*models.TransactionLog, error) {
	dbCtx, cancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer cancel()

	since := time.Now().AddDate(0, -3, 0)

	return s.pgRepo.GetTransactionHistory(dbCtx, merchantID, customerID, since)
}

func (s *DashboardService) GetDashboardStats(ctx context.Context) (*models.DashboardStats, error) {
	dbCtx, cancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer cancel()

	return s.pgRepo.GetDashboardStats(dbCtx)
}
