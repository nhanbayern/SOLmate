package handlers

import (
	"backend/internal/infrastructure"
	"fmt"
	"io"
	"log/slog"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
)

type SSEHandler struct {
	rdb *redis.Client
	log *slog.Logger
}

func NewSSEHandler(rdb *redis.Client) *SSEHandler {
	logger := infrastructure.GetLogger("SSE_HANDLER")

	return &SSEHandler{
		rdb: rdb,
		log: logger,
	}
}

// SubscribeToMerchantStatus godoc
// @Summary      Subscribe to Merchant Status SSE
// @Description   Server-Sent Events endpoint to stream real-time updates for a merchant's applications
// @Tags         loans
// @Accept       json
// @Produce      text/event-stream
// @Security     BearerAuth
// @Param        merchant_id  query      string  true  "Merchant ID"
// @Success      200      {string}  string "SSE stream"
// @Failure      400      {object}  map[string]interface{}
// @Router       /api/loans/stream [get]
func (h *SSEHandler) SubscribeToMerchantStatus(c *gin.Context) {
	merchantID := c.Query("merchant_id")
	if merchantID == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"status": "failed",
			"error":  "merchant_id is required",
		})
		return
	}

	c.Writer.Header().Set("Content-Type", "text/event-stream")
	c.Writer.Header().Set("Cache-Control", "no-cache")
	c.Writer.Header().Set("Connection", "keep-alive")
	c.Writer.Header().Set("Transfer-Encoding", "chunked")
	c.Writer.Header().Set("Access-Control-Allow-Origin", "*")

	ctx := c.Request.Context()
	h.log.Info(
		"Client connect to SSE stream successfully",
		"merchant_id", merchantID,
	)

	channelName := fmt.Sprintf("sse:merchant:%s", merchantID)
	pubsub := h.rdb.Subscribe(ctx, channelName)
	defer pubsub.Close()

	ch := pubsub.Channel()

	c.Stream(func(w io.Writer) bool {
		select {
		case <-ctx.Done():
			h.log.Info(
				"Client disconnected from SSE stream",
				"merchant_id", merchantID,
			)
			return false
		case msg, ok := <-ch:
			if !ok {
				return false
			}

			c.SSEvent("status_update", msg.Payload)
			c.Writer.Flush()

			return true
		}
	})
}
