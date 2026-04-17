package services

import (
	"backend/internal/config"
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var (
	ErrInvalidCredentials = errors.New("invalid username or password")
	ErrUserNotFound       = errors.New("user not found")
)

type UserRepo interface {
	GetByID(ctx context.Context, id string) (*models.User, error)
	GetByUsername(ctx context.Context, username string) (*models.User, error)
}

type AuthService struct {
	userRepo UserRepo
	cfg      config.AuthServiceConfig
	log      *slog.Logger
}

func NewAuthService(userRepo UserRepo, cfg config.AuthServiceConfig) *AuthService {
	logger := infrastructure.GetLogger("AUTH_SERVICE")

	return &AuthService{
		userRepo: userRepo,
		cfg:      cfg,
		log:      logger,
	}
}

type LoginResponse struct {
	AccessToken string          `json:"access_token"`
	TokenType   string          `json:"token_type"`
	ExpiresIn   int64           `json:"expires_in"`
	User        models.AuthUser `json:"user"`
}

func (s *AuthService) Login(ctx context.Context, username, password string) (*LoginResponse, error) {
	s.log.Debug(
		"Login attempt received",
		"username", username,
	)

	dbCtx, cancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer cancel()

	user, err := s.userRepo.GetByUsername(dbCtx, username)
	if err != nil {
		s.log.Error(
			"Fetch user for login failed",
			"username", username,
			infrastructure.KeyError, err.Error(),
		)

		return nil, fmt.Errorf("get user: %w", err)
	}

	if user == nil {
		s.log.Warn(
			"Login failed: user not found",
			"username", username,
		)

		return nil, ErrInvalidCredentials
	}

	if user.PasswordHash != password {
		s.log.Warn(
			"Login failed: invalid password",
			"username", username,
		)

		return nil, ErrInvalidCredentials
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub":  user.ID,
		"exp":  time.Now().Add(s.cfg.JWTExpiration).Unix(),
		"role": user.Role,
	})

	tokenString, err := token.SignedString([]byte(s.cfg.JWTSecret))
	if err != nil {
		s.log.Error(
			"JWT token generation failed",
			"user_id", user.ID,
			infrastructure.KeyError, err.Error(),
		)

		return nil, fmt.Errorf("sign token: %w", err)
	}

	s.log.Info(
		"User logged in successfully",
		"user_id", user.ID,
		"username", user.Username,
	)

	return &LoginResponse{
		AccessToken: tokenString,
		TokenType:   "Bearer",
		ExpiresIn:   int64(s.cfg.JWTExpiration.Seconds()),
		User: models.AuthUser{
			UserID:     user.ID,
			CustomerID: user.CustomerID,
			MerchantID: user.MerchantID,
			Merchant:   user.Merchant,
			Role:       user.Role,
			Status:     user.Status,
		},
	}, nil
}

func (s *AuthService) GetMe(ctx context.Context, userID string) (*models.AuthUser, error) {
	dbCtx, cancel := context.WithTimeout(ctx, s.cfg.DBTimeout)
	defer cancel()

	user, err := s.userRepo.GetByID(dbCtx, userID)
	if err != nil {
		s.log.Error(
			"Fetch user for me failed",
			"user_id", userID,
			infrastructure.KeyError, err.Error(),
		)

		return nil, fmt.Errorf("get user: %w", err)
	}

	if user == nil {
		return nil, ErrUserNotFound
	}

	return &models.AuthUser{
		UserID:     user.ID,
		CustomerID: user.CustomerID,
		MerchantID: user.MerchantID,
		Merchant:   user.Merchant,
		Role:       user.Role,
		Status:     user.Status,
	}, nil
}

func (s *AuthService) ValidateToken(tokenString string) (string, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}

		return []byte(s.cfg.JWTSecret), nil
	})

	if err != nil {
		return "", fmt.Errorf("parse token: %w", err)
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		userID, ok := claims["sub"].(string)
		if !ok {
			return "", errors.New("invalid sub claim in token")
		}

		return userID, nil
	}

	return "", errors.New("invalid or expired token")
}
