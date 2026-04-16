package handlers

import (
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"log/slog"
	"net/http"

	"github.com/gin-gonic/gin"
)

type TransactionDashboardService interface {
	GetTransactions(ctx context.Context, merchantID, customerID string) ([]*models.TransactionLog, error)
}

type TransactionHandler struct {
	service TransactionDashboardService
	log     *slog.Logger
}

func NewTransactionHandler(service TransactionDashboardService) *TransactionHandler {
	logger := infrastructure.GetLogger("TRANSACTION_HANDLER")

	return &TransactionHandler{
		service: service,
		log:     logger,
	}
}

func (h *TransactionHandler) List(c *gin.Context) {
	merchantID := c.Query("merchant_id")
	customerID := c.Query("customer_id")

	if merchantID == "" || customerID == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"status": "failed",
			"error":  "merchant_id and customer_id are required",
		})

		return
	}

	h.log.Debug(
		"List transactions request received",
		"merchant_id", merchantID,
		"customer_id", customerID,
	)

	transactions, err := h.service.GetTransactions(c.Request.Context(), merchantID, customerID)
	if err != nil {
		h.log.Error(
			"List transactions failed",
			"merchant_id", merchantID,
			"customer_id", customerID,
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
		"message": "Transactions fetched successfully",
		"data":    transactions,
	})
}
