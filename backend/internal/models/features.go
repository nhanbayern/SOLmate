package models

type MerchantFeatures struct {
	MerchantID string    `json:"merchant_id"`
	Features   []float64 `json:"features"`
}
