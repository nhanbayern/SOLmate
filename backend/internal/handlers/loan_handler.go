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
	ListLoanRequests(ctx context.Context, limit, offset int) ([]*models.LoanRequest, error)
	GetLoanRequest(ctx context.Context, id string) (*models.LoanRequest, error)
	MakeLoanDecision(ctx context.Context, id string, status string) error
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

// List godoc
// @Summary      List Loan Requests
// @Description   Get all loan evaluation requests and their results
// @Tags         loans
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        limit  query      int  false  "Limit (default 10)"
// @Param        offset query      int  false  "Offset (default 0)"
// @Success      200      {object}  map[string]interface{}
// @Router       /api/loans [get]
func (h *LoanHandler) List(c *gin.Context) {
	limitStr := c.DefaultQuery("limit", "10")
	offsetStr := c.DefaultQuery("offset", "0")

	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit <= 0 {
		limit = 10
	}

	offset, err := strconv.Atoi(offsetStr)
	if err != nil || offset < 0 {
		offset = 0
	}

	h.log.Debug("List loan requests received", "limit", limit, "offset", offset)

	requests, err := h.service.ListLoanRequests(c.Request.Context(), limit, offset)
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

// Get godoc
// @Summary      Get Loan Request Detail
// @Description   Get detailed evaluation results of a specific loan request
// @Tags         loans
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        id   path      string  true  "Loan Request ID" example("LOAN20260417user1")
// @Success      200      {object}  map[string]interface{}
// @Failure      404      {object}  map[string]interface{}
// @Router       /api/loans/{id} [get]
func (h *LoanHandler) Get(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
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

// Decision godoc
// @Summary      Apply Loan Decision
// @Description   Manually approve or reject a loan request after AI evaluation
// @Tags         loans
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        id       path      string  true  "Loan Request ID"
// @Param        request  body      requests.LoanDecisionRequest  true  "Decision payload"
// @Success      200      {object}  map[string]interface{}
// @Failure      400      {object}  map[string]interface{}
// @Router       /api/loans/{id}/decision [post]
func (h *LoanHandler) Decision(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
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
