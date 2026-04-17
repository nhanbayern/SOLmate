package handlers

import (
	"backend/internal/handlers/requests"
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"log/slog"
	"net/http"

	"github.com/gin-gonic/gin"
)

type CustomerDashboardService interface {
	GetCustomerLoans(ctx context.Context, customerID string) ([]*models.LoanRequest, error)
	CreateLoanRequest(ctx context.Context, merchantID, customerID string, loanType string, requestedAmount float64) (*models.LoanRequest, error)
}

type CustomerHandler struct {
	service CustomerDashboardService
	log     *slog.Logger
}

func NewCustomerHandler(service CustomerDashboardService) *CustomerHandler {
	logger := infrastructure.GetLogger("CUSTOMER_HANDLER")

	return &CustomerHandler{
		service: service,
		log:     logger,
	}
}

// ListLoans godoc
// @Summary      List Customer Loan Requests
// @Description   Get all loan evaluation requests for the logged-in customer
// @Tags         customer
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Success      200      {object}  map[string]interface{}
// @Failure      400      {object}  map[string]interface{}
// @Failure      401      {object}  map[string]interface{}
// @Router       /api/customer/loans [get]
func (h *CustomerHandler) ListLoans(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"status": "failed", "error": "Unauthorized"})
		return
	}

	h.log.Debug("List customer loans request received", "customer_id", userID)

	loanRequests, err := h.service.GetCustomerLoans(c.Request.Context(), userID.(string))
	if err != nil {
		h.log.Error(
			"List customer loans failed",
			"customer_id", userID,
			infrastructure.KeyError, err.Error(),
		)

		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error":  "Internal server error",
		})

		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": "Customer loans fetched successfully",
		"data":    loanRequests,
	})
}

// RequestLoan godoc
// @Summary      Create Loan Request
// @Description   Submit a new loan request for the logged-in customer
// @Tags         customer
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        request  body      requests.CreateLoanRequest  true  "Loan request payload"
// @Success      200      {object}  map[string]interface{}
// @Failure      400      {object}  map[string]interface{}
// @Router       /api/customer/loans [post]
func (h *CustomerHandler) RequestLoan(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"status": "failed", "error": "Unauthorized"})
		return
	}

	var req requests.CreateLoanRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		h.log.Error("Bind JSON failed", infrastructure.KeyError, err.Error())
		c.JSON(http.StatusBadRequest, gin.H{
			"status": "failed",
			"error":  "Invalid request payload",
		})
		return
	}

	validLoanTypes := map[string]bool{
		"Khoản vay SME nhỏ":            true,
		"Hạn mức tín dụng quay vòng":   true,
		"Tài trợ hóa đơn đơn giản":     true,
		"Ứng tiền theo doanh thu (MCA)": true,
	}

	if !validLoanTypes[req.LoanType] {
		c.JSON(http.StatusBadRequest, gin.H{
			"status": "failed",
			"error":  "Invalid loan_type. Allowed values are: 'Khoản vay SME nhỏ', 'Hạn mức tín dụng quay vòng', 'Tài trợ hóa đơn đơn giản', 'Ứng tiền theo doanh thu (MCA)'",
		})
		return
	}

	h.log.Debug(
		"Create loan request received",
		"customer_id", userID,
		"merchant_id", req.MerchantID,
		"loan_type", req.LoanType,
		"amount", req.RequestedAmount,
	)

	loan, err := h.service.CreateLoanRequest(c.Request.Context(), req.MerchantID, userID.(string), req.LoanType, req.RequestedAmount)
	if err != nil {
		h.log.Error(
			"Create loan failed",
			"customer_id", userID,
			infrastructure.KeyError, err.Error(),
		)

		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error":  "Internal server error",
		})

		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": "Loan request created successfully",
		"data":    loan,
	})
}
