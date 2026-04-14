package models

type AgentMetrics struct {
	RevenueMean30d float64 `json:"Revenue_mean_30d"`
	RevenueMean90d float64 `json:"Revenue_mean_90d"`
	TxnFrequency   float64 `json:"Txn_frequency"`
	Regime         string  `json:"regime"`
	GrowthValue    float64 `json:"Growth_value"`
	GrowthScore    float64 `json:"Growth_score"`
	CVValue        float64 `json:"CV_value"`
	CVScore        float64 `json:"CV_score"`
	SpikeRatio     float64 `json:"Spike_ratio"`
	SpikeScore     float64 `json:"Spike_score"`
	TxnFreqScore   float64 `json:"Txn_freq_score"`
	YearsScore     float64 `json:"Years_score"`
	IndustryScore  float64 `json:"Industry_score"`
}

type AgentRiskRequest struct {
	CustomerID      string       `json:"customer_id"`
	CreditScore     float64      `json:"credit_score"`
	Metrics         AgentMetrics `json:"metrics"`
	RiskClass       string       `json:"risk_class"`
	RiskProbability float64      `json:"risk_probability"`
}

type AgentRiskResponse struct {
	CustomerID                  string   `json:"customer_id"`
	ProvidedRiskClass           string   `json:"provided_risk_class"`
	ExpectedRiskClass           string   `json:"expected_risk_class"`
	ProvidedRiskProbability     float64  `json:"provided_risk_probability"`
	ExpectedRiskProbability     float64  `json:"expected_risk_probability"`
	ExpectedProbabilityBand     string   `json:"expected_probability_band"`
	RiskClassIsReasonable       bool     `json:"risk_class_is_reasonable"`
	RiskProbabilityIsReasonable bool     `json:"risk_probability_is_reasonable"`
	Recommendation              string   `json:"recommendation"`
	Summary                     string   `json:"summary"`
	Findings                    []string `json:"findings"`
	ReportText                  string   `json:"report_text"`
}
