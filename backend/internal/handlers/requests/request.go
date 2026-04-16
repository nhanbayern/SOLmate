package requests

type EvaluateLoanRequest struct {
	LoanID     int    `json:"loan_id" binding:"required"`
	MerchantID string `json:"merchant_id" binding:"required"`
	CustomerID string `json:"customer_id" binding:"required"`
}
