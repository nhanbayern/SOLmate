package handlers

import (
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"log/slog"
	"net/http"

	"github.com/gin-gonic/gin"
)

type MerchantDashboardService interface {
	ListMerchants(ctx context.Context) ([]*models.Merchant, error)
	GetMerchant(ctx context.Context, id string) (*models.Merchant, error)
}

type MerchantHandler struct {
	service MerchantDashboardService
	log     *slog.Logger
}

func NewMerchantHandler(service MerchantDashboardService) *MerchantHandler {
	logger := infrastructure.GetLogger("MERCHANT_HANDLER")

	return &MerchantHandler{
		service: service,
		log:     logger,
	}
}

// List godoc
// @Summary      List Merchants
// @Description   Get all merchants with their basic metadata
// @Tags         merchants
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Success      200      {object}  map[string]interface{}
// @Router       /api/merchants [get]
func (h *MerchantHandler) List(c *gin.Context) {
	h.log.Debug("List merchants request received")

	merchants, err := h.service.ListMerchants(c.Request.Context())
	if err != nil {
		h.log.Error("List merchants failed", infrastructure.KeyError, err.Error())

		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error":  "Internal server error",
		})

		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": "Merchants fetched successfully",
		"data":    merchants,
	})
}

// Get godoc
// @Summary      Get Merchant Detailed
// @Description   Get detailed metadata of a specific merchant by ID
// @Tags         merchants
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        id   path      string  true  "Merchant ID"
// @Success      200      {object}  map[string]interface{}
// @Failure      404      {object}  map[string]interface{}
// @Router       /api/merchants/{id} [get]
func (h *MerchantHandler) Get(c *gin.Context) {
	id := c.Param("id")

	h.log.Debug(
		"Get merchant request received",
		"merchant_id", id,
	)

	merchant, err := h.service.GetMerchant(c.Request.Context(), id)
	if err != nil {
		h.log.Error(
			"Get merchant failed",
			"merchant_id", id,
			infrastructure.KeyError, err.Error(),
		)

		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error":  "Internal server error",
		})

		return
	}

	if merchant == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"status": "failed",
			"error":  "Merchant not found",
		})

		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": "Merchant fetched successfully",
		"data":    merchant,
	})
}
