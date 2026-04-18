package models

import "time"

type LoanRequest struct {
	ID              string    `json:"id"`
	MerchantID      string    `json:"merchant_id"`
	CustomerID      string    `json:"customer_id"`
	LoanType        string    `json:"loan_type"`
	RequestedAmount float64   `json:"requested_amount"`
	AIScore         int       `json:"ai_score"`
	RiskLabel       string    `json:"risk_label"`
	PDValue         float64   `json:"pd_value"`
	AIAgentReport   string    `json:"ai_agent_report"`
	Status          string    `json:"status"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

type EvaluationResult struct {
	LoanID         string        `json:"loan_id"`
	MerchantID     string        `json:"merchant_id"`
	CustomerID     string        `json:"customer_id"`
	Score          int           `json:"score"`
	RiskLabel      string        `json:"risk_label"`
	PDValue        float64       `json:"pd_value"`
	Recommendation string        `json:"recommendation"`
	ReportText     string        `json:"report_text"`
	Metrics        []float64     `json:"metrics"`
	AgentMetrics   *AgentMetrics `json:"agent_metrics"`
}
