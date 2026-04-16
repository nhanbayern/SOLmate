package handlers

import (
	"backend/internal/handlers/requests"
	"backend/internal/infrastructure"
	"context"
	"log/slog"
	"net/http"

	"github.com/gin-gonic/gin"
)

type LoanService interface {
	EvaluateLoan(ctx context.Context, loanID int, merchantID, customerID string) error
}

type HTTPHandler struct {
	loanService LoanService
	log         *slog.Logger
}

func NewHTTPHandler(loanService LoanService) *HTTPHandler {
	logger := infrastructure.GetLogger("LOAN_HANDLER")

	return &HTTPHandler{
		loanService: loanService,
		log:         logger,
	}
}

func (h *HTTPHandler) EvaluateLoan(c *gin.Context) {
	var req requests.EvaluateLoanRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		h.log.Error(
			"Bind JSON failed",
			infrastructure.KeyError, err.Error(),
		)

		c.JSON(http.StatusBadRequest, gin.H{
			"status": "failed",
			"error":  "Invalid request payload",
		})

		return
	}

	h.log.Debug(
		"Evaluate loan request received",
		"loan_id", req.LoanID,
		"merchant_id", req.MerchantID,
		"customer_id", req.CustomerID,
	)

	err := h.loanService.EvaluateLoan(c.Request.Context(), req.LoanID, req.MerchantID, req.CustomerID)
	if err != nil {
		h.log.Error(
			"Evaluate loan failed",
			"loan_id", req.LoanID,
			"merchant_id", req.MerchantID,
			"customer_id", req.CustomerID,
			infrastructure.KeyError, err.Error(),
		)

		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error":  "Internal server error",
		})

		return
	}

	h.log.Info(
		"Evaluate loan request successfully",
		"loan_id", req.LoanID,
		"merchant_id", req.MerchantID,
		"customer_id", req.CustomerID,
	)

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": "Loan evaluated successfully",
	})
}
