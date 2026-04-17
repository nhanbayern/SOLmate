package handlers

import (
	"backend/internal/handlers/requests"
	"backend/internal/infrastructure"
	"backend/internal/models"
	"backend/internal/services"
	"context"
	"log/slog"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

type AuthService interface {
	Login(ctx context.Context, username, password string) (*services.LoginResponse, error)
	GetMe(ctx context.Context, userID string) (*models.AuthUser, error)
	ValidateToken(tokenString string) (string, error)
}

type AuthHandler struct {
	authService AuthService
	log         *slog.Logger
}

func NewAuthHandler(authService AuthService) *AuthHandler {
	logger := infrastructure.GetLogger("AUTH_HANDLER")

	return &AuthHandler{
		authService: authService,
		log:         logger,
	}
}

// Login godoc
// @Summary      User Login
// @Description   Authenticate user and return JWT token
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        request  body      requests.LoginRequest  true  "Login credentials"
// @Success      200      {object}  map[string]interface{}
// @Failure      401      {object}  map[string]interface{}
// @Router       /api/auth/login [post]
func (h *AuthHandler) Login(c *gin.Context) {
	var req requests.LoginRequest
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
		"Login request received",
		"user_id", req.UserID,
	)

	result, err := h.authService.Login(c.Request.Context(), req.UserID, req.Password)
	if err != nil {
		if err == services.ErrInvalidCredentials {
			c.JSON(http.StatusUnauthorized, gin.H{
				"status": "failed",
				"error":  "Invalid credentials",
			})

			return
		}

		h.log.Error(
			"Login failed",
			"user_id", req.UserID,
			infrastructure.KeyError, err.Error(),
		)

		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error":  "Internal server error",
		})

		return
	}

	h.log.Info(
		"User logged in successfully",
		"user_id", result.User.UserID,
	)

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": "Logged in successfully",
	})
}

// Me godoc
// @Summary      Get Current User
// @Description   Return current authenticated user profile
// @Tags         auth
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Success      200      {object}  map[string]interface{}
// @Failure      401      {object}  map[string]interface{}
// @Router       /api/auth/me [get]
func (h *AuthHandler) Me(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		h.log.Warn("Attempted to access Me without user_id in context")

		c.JSON(http.StatusUnauthorized, gin.H{
			"status": "failed",
			"error":  "Unauthorized",
		})

		return
	}

	_, err := h.authService.GetMe(c.Request.Context(), userID.(string))
	if err != nil {
		h.log.Error(
			"GetMe failed",
			"user_id", userID,
			infrastructure.KeyError, err.Error(),
		)

		c.JSON(http.StatusNotFound, gin.H{
			"status": "error",
			"error":  "User not found",
		})

		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": "User profile fetched successfully",
	})
}

func (h *AuthHandler) AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{
				"status": "failed",
				"error":  "Authorization header required",
			})

			c.Abort()

			return
		}

		tokenParts := strings.Split(authHeader, " ")
		if len(tokenParts) != 2 || tokenParts[0] != "Bearer" {
			c.JSON(http.StatusUnauthorized, gin.H{
				"status": "failed",
				"error":  "Invalid authorization format",
			})

			c.Abort()

			return
		}

		userID, err := h.authService.ValidateToken(tokenParts[1])
		if err != nil {
			h.log.Warn(
				"Token validation failed",
				infrastructure.KeyError, err.Error(),
			)

			c.JSON(http.StatusUnauthorized, gin.H{
				"status": "failed",
				"error":  "Invalid or expired token",
			})

			c.Abort()

			return
		}

		c.Set("user_id", userID)
		c.Next()
	}
}
