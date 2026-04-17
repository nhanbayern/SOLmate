package models

type AgentMetrics map[string]any

type EnterpriseProfile struct {
	CustomerID      string  `json:"customer_id"`
	MerchantID      string  `json:"merchant_id"`
	Name            string  `json:"name"`
	Age             int     `json:"age,omitempty"`
	Industry        string  `json:"industry"`
	BusinessType    string  `json:"business_type"`
	YearsInBusiness float64 `json:"years_in_business"`
	Location        string  `json:"location,omitempty"`
	CreatedAt       string  `json:"created_at"`
}

type EnterpriseCICMetrics struct {
	CustomerID      string       `json:"customer_id"`
	CreditScore     float64      `json:"credit_score"`
	Metrics         AgentMetrics `json:"metrics"`
	RiskClass       string       `json:"risk_class"`
	RiskProbability float64      `json:"risk_probability"`
}

type AgentRiskRequest struct {
	EnterpriseProfile    EnterpriseProfile    `json:"enterprise_profile"`
	EnterpriseCICMetrics EnterpriseCICMetrics `json:"enterprise_cic_metrics"`
}

type AgentRiskResponse struct {
	CustomerID     string `json:"customer_id"`
	ReportTextUser string `json:"report_text_user"`
	ReportTextBank string `json:"report_text_bank"`
}
