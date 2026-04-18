package requests

type EvaluateLoanRequest struct {
	LoanID     string `json:"loan_id" binding:"required" example:"LOAN20260417152817user19096"`
	MerchantID string `json:"merchant_id" binding:"required" example:"MER_52153584"`
	CustomerID string `json:"customer_id" binding:"required" example:"CUST_68057522"`
}

type CreateLoanRequest struct {
	MerchantID      string  `json:"merchant_id" binding:"required" example:"MER_52153584"`
	LoanType        string  `json:"loan_type" binding:"required" example:"Khoản vay SME nhỏ"`
	RequestedAmount float64 `json:"requested_amount" binding:"required,gt=0" example:"50000"`
}

type LoginRequest struct {
	Username string `json:"username" binding:"required" example:"admin"`
	Password string `json:"password" binding:"required" example:"admin"`
}

type LoanDecisionRequest struct {
	Status string `json:"status" binding:"required,oneof=APPROVED REJECTED"`
}
