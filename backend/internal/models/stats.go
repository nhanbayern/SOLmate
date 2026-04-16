package models

type DashboardStats struct {
	TotalRequests       int            `json:"total_requests"`
	TotalApprovedAmount float64        `json:"total_approved_amount"`
	ApprovalRate        float64        `json:"approval_rate"`
	RiskDistribution    map[string]int `json:"risk_distribution"`
}
