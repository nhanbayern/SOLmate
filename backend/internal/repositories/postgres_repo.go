package repositories

import (
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"database/sql"
	"fmt"
	"log/slog"
	"time"
)

type PostgresRepo struct {
	db  *sql.DB
	log *slog.Logger
}

func NewPostgresRepo(db *sql.DB) *PostgresRepo {
	logger := infrastructure.GetLogger("POSTGRES_REPO")

	return &PostgresRepo{
		db:  db,
		log: logger,
	}
}

func (r *PostgresRepo) InsertTransactionLog(ctx context.Context, log *models.TransactionLog) error {
	query := `
	INSERT INTO transaction_logs (merchant_id, customer_id, amount, is_refund, pos_terminal_id)
		VALUES ($1, $2, $3, $4, $5)
		RETURNING id, transaction_time, created_at
	`

	if err := r.db.QueryRowContext(ctx, query,
		log.MerchantID, log.CustomerID, log.Amount, log.IsRefund, log.POSTerminalID,
	).Scan(&log.ID, &log.TransactionTime, &log.CreatedAt); err != nil {
		return fmt.Errorf("insert transaction log: %w", err)
	}

	r.log.Debug(
		"Transaction saved successfully",
		"id", log.ID,
		"merchant_id", log.MerchantID,
		"customer_id", log.CustomerID,
		"amount", log.Amount,
		"is_refund", log.IsRefund,
		"pos_terminal_id", log.POSTerminalID,
	)

	return nil
}

func (r *PostgresRepo) GetMerchantMetadata(ctx context.Context, id string) (*models.Merchant, error) {
	query := `
	SELECT id, name, business_type, industry, years_in_business, owner_name, kyc_status, created_at, updated_at
		FROM merchants
		WHERE id = $1
	`

	var merchant models.Merchant
	if err := r.db.QueryRowContext(ctx, query, id).Scan(
		&merchant.ID,
		&merchant.Name,
		&merchant.BusinessType,
		&merchant.Industry,
		&merchant.YearsInBusiness,
		&merchant.OwnerName,
		&merchant.KYCStatus,
		&merchant.CreatedAt,
		&merchant.UpdatedAt,
	); err != nil {
		return nil, fmt.Errorf("get merchant meta: %w", err)
	}

	r.log.Debug(
		"Get merchant metadata successfully",
		"merchant_id", merchant.ID,
		"merchant_name", merchant.Name,
		"business_type", merchant.BusinessType,
		"industry", merchant.Industry,
		"year_in_business", merchant.YearsInBusiness,
		"owner_name", merchant.OwnerName,
		"kyc_status", merchant.KYCStatus,
	)

	return &merchant, nil
}

func (r *PostgresRepo) GetTransactionHistory(ctx context.Context, merchantID, customerID string, since time.Time) ([]*models.TransactionLog, error) {
	query := `
	SELECT id, merchant_id, customer_id, amount, is_refund, pos_terminal_id, transaction_time, created_at
		FROM transaction_logs
		WHERE merchant_id = $1 AND customer_id = $2 AND transaction_time >= $3
		ORDER BY transaction_time ASC
	`

	rows, err := r.db.QueryContext(ctx, query, merchantID, customerID, since)
	if err != nil {
		return nil, fmt.Errorf("query transaction history: %w", err)
	}
	defer rows.Close()

	var logs []*models.TransactionLog
	for rows.Next() {
		var l models.TransactionLog
		if err := rows.Scan(
			&l.ID, &l.MerchantID, &l.CustomerID, &l.Amount, &l.IsRefund, &l.POSTerminalID, &l.TransactionTime, &l.CreatedAt,
		); err != nil {
			return nil, fmt.Errorf("scan transaction log: %w", err)
		}
		logs = append(logs, &l)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("rows error: %w", err)
	}

	r.log.Debug(
		"Get transaction history successfully",
		"merchant_id", merchantID,
		"customer_id", customerID,
		"since", since,
	)

	return logs, nil
}

func (r *PostgresRepo) UpdateLoanAIReport(
	ctx context.Context,
	loanID, score int,
	riskLabel string,
	pdValue float64,
	report string,
) error {
	query := `
	UPDATE loan_requests 
		SET ai_score = $1, risk_label = $2, pd_value = $3, ai_agent_report = $4, status = 'APPROVED', updated_at = CURRENT_TIMESTAMP
		WHERE id = $5
	`

	result, err := r.db.ExecContext(ctx, query, score, riskLabel, pdValue, report, loanID)
	if err != nil {
		return fmt.Errorf("update loan report: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		r.log.Warn(
			"Loan AI report not found to update",
			"loan_id", loanID,
			"score", score,
			"risk_label", riskLabel,
			"pd_value", pdValue,
		)

		return fmt.Errorf("loan not found")
	}

	r.log.Debug(
		"Loan AI report updated successfully",
		"loan_id", loanID,
		"score", score,
		"risk_label", riskLabel,
		"pd_value", pdValue,
	)

	return nil
}
