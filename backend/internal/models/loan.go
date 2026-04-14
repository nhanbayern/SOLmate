package models

import "time"

type LoanRequest struct {
	ID              int       `json:"id"`
	MerchantID      string    `json:"merchant_id"`
	RequestedAmount float64   `json:"requested_amount"`
	AIScore         int       `json:"ai_score"`
	RiskLabel       string    `json:"risk_label"`
	PDValue         float64   `json:"pd_value"`
	AIAgentReport   string    `json:"ai_agent_report"`
	Status          string    `json:"status"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}
