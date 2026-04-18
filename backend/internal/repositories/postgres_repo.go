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

func (r *PostgresRepo) GetAllMerchants(ctx context.Context) ([]*models.Merchant, error) {
	query := `
	SELECT id, name, business_type, industry, years_in_business, owner_name, kyc_status, created_at, updated_at
		FROM merchants
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("query all merchants: %w", err)
	}
	defer rows.Close()

	var merchants []*models.Merchant
	for rows.Next() {
		var m models.Merchant
		if err := rows.Scan(
			&m.ID, &m.Name, &m.BusinessType, &m.Industry, &m.YearsInBusiness, &m.OwnerName, &m.KYCStatus, &m.CreatedAt, &m.UpdatedAt,
		); err != nil {
			return nil, fmt.Errorf("scan merchant: %w", err)
		}
		merchants = append(merchants, &m)
	}

	r.log.Debug(
		"Fetch all merchants successfully",
		"count", len(merchants),
	)

	return merchants, nil
}

func (r *PostgresRepo) GetAllLoanRequests(ctx context.Context, limit, offset int) ([]*models.LoanRequest, error) {
	query := `
	SELECT id, merchant_id, customer_id, loan_type, requested_amount, ai_score, risk_label, pd_value, ai_agent_report, status, created_at, updated_at
		FROM loan_requests
		ORDER BY created_at DESC
		LIMIT $1 OFFSET $2
	`

	rows, err := r.db.QueryContext(ctx, query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("query all loan requests: %w", err)
	}
	defer rows.Close()

	requests := make([]*models.LoanRequest, 0)
	for rows.Next() {
		var req models.LoanRequest
		var aiScore sql.NullInt32
		var riskLabel, aiAgentReport sql.NullString
		var pdValue sql.NullFloat64

		if err := rows.Scan(
			&req.ID, &req.MerchantID, &req.CustomerID, &req.LoanType, &req.RequestedAmount, &aiScore, &riskLabel, &pdValue, &aiAgentReport, &req.Status, &req.CreatedAt, &req.UpdatedAt,
		); err != nil {
			return nil, fmt.Errorf("scan loan request: %w", err)
		}

		if aiScore.Valid {
			req.AIScore = int(aiScore.Int32)
		}
		if riskLabel.Valid {
			req.RiskLabel = riskLabel.String
		}
		if pdValue.Valid {
			req.PDValue = pdValue.Float64
		}
		if aiAgentReport.Valid {
			req.AIAgentReport = aiAgentReport.String
		}

		requests = append(requests, &req)
	}

	r.log.Debug(
		"Fetch all loan requests successfully",
		"count", len(requests),
	)

	return requests, nil
}

func (r *PostgresRepo) GetLoanRequestsByCustomer(ctx context.Context, customerID string) ([]*models.LoanRequest, error) {
	query := `
	SELECT id, merchant_id, customer_id, loan_type, requested_amount, ai_score, risk_label, pd_value, ai_agent_report, status, created_at, updated_at
		FROM loan_requests
		WHERE customer_id = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.QueryContext(ctx, query, customerID)
	if err != nil {
		return nil, fmt.Errorf("query customer loan requests: %w", err)
	}
	defer rows.Close()

	requests := make([]*models.LoanRequest, 0)
	for rows.Next() {
		var req models.LoanRequest
		var aiScore sql.NullInt32
		var riskLabel, aiAgentReport sql.NullString
		var pdValue sql.NullFloat64

		if err := rows.Scan(
			&req.ID, &req.MerchantID, &req.CustomerID, &req.LoanType, &req.RequestedAmount, &aiScore, &riskLabel, &pdValue, &aiAgentReport, &req.Status, &req.CreatedAt, &req.UpdatedAt,
		); err != nil {
			return nil, fmt.Errorf("scan customer loan request: %w", err)
		}

		if aiScore.Valid {
			req.AIScore = int(aiScore.Int32)
		}
		if riskLabel.Valid {
			req.RiskLabel = riskLabel.String
		}
		if pdValue.Valid {
			req.PDValue = pdValue.Float64
		}
		if aiAgentReport.Valid {
			req.AIAgentReport = aiAgentReport.String
		}

		requests = append(requests, &req)
	}

	r.log.Debug(
		"Fetch customer loan requests successfully",
		"customer_id", customerID,
		"count", len(requests),
	)

	return requests, nil
}

func (r *PostgresRepo) GetLoanRequestByID(ctx context.Context, id string) (*models.LoanRequest, error) {
	query := `
	SELECT id, merchant_id, customer_id, loan_type, requested_amount, ai_score, risk_label, pd_value, ai_agent_report, status, created_at, updated_at
		FROM loan_requests
		WHERE id = $1
	`

	var req models.LoanRequest
	var aiScore sql.NullInt32
	var riskLabel, aiAgentReport sql.NullString
	var pdValue sql.NullFloat64

	if err := r.db.QueryRowContext(ctx, query, id).Scan(
		&req.ID, &req.MerchantID, &req.CustomerID, &req.LoanType, &req.RequestedAmount, &aiScore, &riskLabel, &pdValue, &aiAgentReport, &req.Status, &req.CreatedAt, &req.UpdatedAt,
	); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("get loan request by id: %w", err)
	}

	if aiScore.Valid {
		req.AIScore = int(aiScore.Int32)
	}
	if riskLabel.Valid {
		req.RiskLabel = riskLabel.String
	}
	if pdValue.Valid {
		req.PDValue = pdValue.Float64
	}
	if aiAgentReport.Valid {
		req.AIAgentReport = aiAgentReport.String
	}

	r.log.Debug(
		"Fetch loan request by ID successfully",
		"loan_id", id,
	)

	return &req, nil
}

func (r *PostgresRepo) InsertLoanRequest(ctx context.Context, merchantID, customerID string, loanType string, requestedAmount float64) (*models.LoanRequest, error) {
	loanID := fmt.Sprintf("LOAN%s%s", time.Now().Format("20060102150405"), customerID)

	query := `
	INSERT INTO loan_requests (id, merchant_id, customer_id, loan_type, requested_amount, status)
		VALUES ($1, $2, $3, $4, $5, 'PENDING')
		RETURNING id, merchant_id, customer_id, loan_type, requested_amount, status, created_at, updated_at
	`

	var req models.LoanRequest
	if err := r.db.QueryRowContext(ctx, query, loanID, merchantID, customerID, loanType, requestedAmount).Scan(
		&req.ID, &req.MerchantID, &req.CustomerID, &req.LoanType, &req.RequestedAmount, &req.Status, &req.CreatedAt, &req.UpdatedAt,
	); err != nil {
		return nil, fmt.Errorf("insert loan request: %w", err)
	}

	r.log.Debug(
		"Loan request created successfully",
		"loan_id", req.ID,
	)

	return &req, nil
}

func (r *PostgresRepo) GetDashboardStats(ctx context.Context) (*models.DashboardStats, error) {
	var totalRequests int
	err := r.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM loan_requests").Scan(&totalRequests)
	if err != nil {
		return nil, fmt.Errorf("count loan requests: %w", err)
	}

	var totalApprovedAmount sql.NullFloat64
	err = r.db.QueryRowContext(ctx, "SELECT SUM(requested_amount) FROM loan_requests WHERE status = 'APPROVED'").Scan(&totalApprovedAmount)
	if err != nil {
		return nil, fmt.Errorf("sum approved amount: %w", err)
	}

	var totalApproved int
	err = r.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM loan_requests WHERE status = 'APPROVED'").Scan(&totalApproved)
	if err != nil {
		return nil, fmt.Errorf("count approved: %w", err)
	}

	approvalRate := 0.0
	if totalRequests > 0 {
		approvalRate = float64(totalApproved) / float64(totalRequests) * 100.0
	}

	riskDistribution := make(map[string]int)
	rows, err := r.db.QueryContext(ctx, "SELECT risk_label, COUNT(*) FROM loan_requests WHERE risk_label IS NOT NULL GROUP BY risk_label")
	if err != nil {
		return nil, fmt.Errorf("query risk distribution: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var riskLabel string
		var count int
		if err := rows.Scan(&riskLabel, &count); err != nil {
			return nil, fmt.Errorf("scan risk distribution: %w", err)
		}
		riskDistribution[riskLabel] = count
	}

	r.log.Debug("Fetch dashboard stats successfully")

	return &models.DashboardStats{
		TotalRequests:       totalRequests,
		TotalApprovedAmount: totalApprovedAmount.Float64,
		ApprovalRate:        approvalRate,
		RiskDistribution:    riskDistribution,
	}, nil
}

func (r *PostgresRepo) UpdateLoanAIReport(
	ctx context.Context,
	loanID string, score int,
	riskLabel string,
	pdValue float64,
	report string,
) error {
	query := `
	UPDATE loan_requests
		SET ai_score = $1, risk_label = $2, pd_value = $3, ai_agent_report = $4, status = 'EVALUATED', updated_at = CURRENT_TIMESTAMP
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

func (r *PostgresRepo) UpdateLoanStatus(ctx context.Context, id string, status string) error {
	query := `
	UPDATE loan_requests
		SET status = $1, updated_at = CURRENT_TIMESTAMP
		WHERE id = $2
	`

	result, err := r.db.ExecContext(ctx, query, status, id)
	if err != nil {
		return fmt.Errorf("update loan status: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("loan not found")
	}

	r.log.Debug(
		"Loan status updated successfully",
		"loan_id", id,
		"status", status,
	)

	return nil
}
