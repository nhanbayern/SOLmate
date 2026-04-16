package requests

type EvaluateLoanRequest struct {
	LoanID     int    `json:"loan_id" binding:"required"`
	MerchantID string `json:"merchant_id" binding:"required"`
	CustomerID string `json:"customer_id" binding:"required"`
}

type LoginRequest struct {
	UserID   string `json:"user_id"`
	Password string `json:"password"`
}

type LoanDecisionRequest struct {
	Status string `json:"status" binding:"required,oneof=APPROVED REJECTED"`
}
