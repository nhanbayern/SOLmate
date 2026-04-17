package repositories

import (
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"database/sql"
	"fmt"
	"log/slog"
)

type UserRepo struct {
	db  *sql.DB
	log *slog.Logger
}

func NewUserRepo(db *sql.DB) *UserRepo {
	logger := infrastructure.GetLogger("USER_REPO")

	return &UserRepo{
		db:  db,
		log: logger,
	}
}

func (r *UserRepo) GetByUsername(ctx context.Context, username string) (*models.User, error) {
	query := `
	SELECT user_id, username, password_hash, role, merchant_id, customer_id, status, created_at, updated_at
		FROM users
		WHERE username = $1
	`

	var user models.User
	if err := r.db.QueryRowContext(ctx, query, username).Scan(
		&user.ID,
		&user.Username,
		&user.PasswordHash,
		&user.Role,
		&user.MerchantID,
		&user.CustomerID,
		&user.Status,
		&user.CreatedAt,
		&user.UpdatedAt,
	); err != nil {
		if err == sql.ErrNoRows {
			r.log.Debug(
				"User not found by username",
				"username", username,
			)

			return nil, nil
		}

		r.log.Error(
			"Fetch user by username failed",
			"username", username,
			infrastructure.KeyError, err.Error(),
		)

		return nil, fmt.Errorf("get user by username: %w", err)
	}

	r.log.Debug(
		"Fetched user by username successfully",
		"user_id", user.ID,
		"username", user.Username,
	)

	return &user, nil
}

func (r *UserRepo) GetByID(ctx context.Context, id string) (*models.User, error) {
	query := `
	SELECT user_id, username, password_hash, role, merchant_id, customer_id, status, created_at, updated_at
		FROM users
		WHERE user_id = $1
	`

	var user models.User
	if err := r.db.QueryRowContext(ctx, query, id).Scan(
		&user.ID,
		&user.Username,
		&user.PasswordHash,
		&user.Role,
		&user.MerchantID,
		&user.CustomerID,
		&user.Status,
		&user.CreatedAt,
		&user.UpdatedAt,
	); err != nil {
		if err == sql.ErrNoRows {
			r.log.Debug(
				"User not found by ID",
				"user_id", id,
			)

			return nil, nil
		}

		r.log.Error(
			"Fetch user by ID failed",
			"user_id", id,
			infrastructure.KeyError, err.Error(),
		)

		return nil, fmt.Errorf("get user by id: %w", err)
	}

	r.log.Debug(
		"Fetched user by ID successfully",
		"user_id", user.ID,
		"username", user.Username,
	)

	return &user, nil
}
