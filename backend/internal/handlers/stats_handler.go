package handlers

import (
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"log/slog"
	"net/http"

	"github.com/gin-gonic/gin"
)

type StatsDashboardService interface {
	GetDashboardStats(ctx context.Context) (*models.DashboardStats, error)
}

type StatsHandler struct {
	service StatsDashboardService
	log     *slog.Logger
}

func NewStatsHandler(service StatsDashboardService) *StatsHandler {
	logger := infrastructure.GetLogger("STATS_HANDLER")

	return &StatsHandler{
		service: service,
		log:     logger,
	}
}

func (h *StatsHandler) Get(c *gin.Context) {
	h.log.Debug("Get stats request received")

	stats, err := h.service.GetDashboardStats(c.Request.Context())
	if err != nil {
		h.log.Error(
			"Get dashboard stats failed",
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
		"message": "Dashboard stats fetched successfully",
		"data":    stats,
	})
}
