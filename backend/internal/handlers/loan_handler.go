package handlers

import (
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"log/slog"
	"net/http"
	"strconv"

	"backend/internal/handlers/requests"

	"github.com/gin-gonic/gin"
)

type LoanDashboardService interface {
	ListLoanRequests(ctx context.Context) ([]*models.LoanRequest, error)
	GetLoanRequest(ctx context.Context, id int) (*models.LoanRequest, error)
	MakeLoanDecision(ctx context.Context, id int, status string) error
}

type LoanHandler struct {
	service LoanDashboardService
	log     *slog.Logger
}

func NewLoanHandler(service LoanDashboardService) *LoanHandler {
	logger := infrastructure.GetLogger("LOAN_DASHBOARD_HANDLER")

	return &LoanHandler{
		service: service,
		log:     logger,
	}
}

func (h *LoanHandler) List(c *gin.Context) {
	h.log.Debug("List loan requests received")

	requests, err := h.service.ListLoanRequests(c.Request.Context())
	if err != nil {
		h.log.Error(
			"List loan requests failed",
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
		"message": "Loan requests fetched successfully",
		"data":    requests,
	})
}

func (h *LoanHandler) Get(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status": "failed",
			"error":  "Invalid loan ID",
		})
		return
	}

	h.log.Debug(
		"Get loan request received",
		"loan_id", id,
	)

	req, err := h.service.GetLoanRequest(c.Request.Context(), id)
	if err != nil {
		h.log.Error(
			"Get loan request failed",
			"loan_id", id,
			infrastructure.KeyError, err.Error(),
		)

		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error":  "Internal server error",
		})

		return
	}

	if req == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"status": "failed",
			"error":  "Loan request not found",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": "Loan request fetched successfully",
		"data":    req,
	})
}

func (h *LoanHandler) Decision(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status": "failed",
			"error":  "Invalid loan ID",
		})
		return
	}

	var req requests.LoanDecisionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status": "failed",
			"error":  "Invalid request payload",
		})
		return
	}

	h.log.Debug(
		"Loan decision request received",
		"loan_id", id,
		"decision", req.Status,
	)

	if err := h.service.MakeLoanDecision(c.Request.Context(), id, req.Status); err != nil {
		h.log.Error(
			"Make loan decision failed",
			"loan_id", id,
			infrastructure.KeyError, err.Error(),
		)

		status := http.StatusInternalServerError
		if err.Error() == "loan not found" {
			status = http.StatusNotFound
		}

		c.JSON(status, gin.H{
			"status": "error",
			"error":  "Update loan status failed",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": "Loan decision applied successfully",
	})
}
