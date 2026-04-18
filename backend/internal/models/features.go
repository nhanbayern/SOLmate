package models

type MerchantFeatures struct {
	MerchantID string    `json:"merchant_id"`
	CustomerID string    `json:"customer_id"`
	Features   []float64 `json:"features"`
}
