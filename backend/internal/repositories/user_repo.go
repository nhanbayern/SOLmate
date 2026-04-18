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
	SELECT
		u.user_id, u.username, u.password_hash, u.role, u.merchant_id, u.customer_id, u.status, u.created_at, u.updated_at,
		m.id, m.name, m.business_type, m.industry, m.years_in_business, m.owner_name, m.kyc_status, m.created_at, m.updated_at
	FROM users u
	LEFT JOIN merchants m ON u.merchant_id = m.id
	WHERE u.username = $1
	`

	var user models.User
	var mID, mName, mBusinessType, mIndustry, mOwnerName, mKycStatus sql.NullString
	var mYearsInBusiness sql.NullInt32
	var mCreatedAt, mUpdatedAt sql.NullTime

	if err := r.db.QueryRowContext(ctx, query, username).Scan(
		&user.ID, &user.Username, &user.PasswordHash, &user.Role, &user.MerchantID, &user.CustomerID, &user.Status, &user.CreatedAt, &user.UpdatedAt,
		&mID, &mName, &mBusinessType, &mIndustry, &mYearsInBusiness, &mOwnerName, &mKycStatus, &mCreatedAt, &mUpdatedAt,
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

	if mID.Valid {
		user.Merchant = &models.Merchant{
			ID:              mID.String,
			Name:            mName.String,
			BusinessType:    mBusinessType.String,
			Industry:        mIndustry.String,
			YearsInBusiness: int(mYearsInBusiness.Int32),
			OwnerName:       mOwnerName.String,
			KYCStatus:       mKycStatus.String,
			CreatedAt:       mCreatedAt.Time,
			UpdatedAt:       mUpdatedAt.Time,
		}
	}

	return &user, nil
}

func (r *UserRepo) GetByID(ctx context.Context, id string) (*models.User, error) {
	query := `
	SELECT
		u.user_id, u.username, u.password_hash, u.role, u.merchant_id, u.customer_id, u.status, u.created_at, u.updated_at,
		m.id, m.name, m.business_type, m.industry, m.years_in_business, m.owner_name, m.kyc_status, m.created_at, m.updated_at
	FROM users u
	LEFT JOIN merchants m ON u.merchant_id = m.id
	WHERE u.user_id = $1
	`

	var user models.User
	var mID, mName, mBusinessType, mIndustry, mOwnerName, mKycStatus sql.NullString
	var mYearsInBusiness sql.NullInt32
	var mCreatedAt, mUpdatedAt sql.NullTime

	if err := r.db.QueryRowContext(ctx, query, id).Scan(
		&user.ID, &user.Username, &user.PasswordHash, &user.Role, &user.MerchantID, &user.CustomerID, &user.Status, &user.CreatedAt, &user.UpdatedAt,
		&mID, &mName, &mBusinessType, &mIndustry, &mYearsInBusiness, &mOwnerName, &mKycStatus, &mCreatedAt, &mUpdatedAt,
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

	if mID.Valid {
		user.Merchant = &models.Merchant{
			ID:              mID.String,
			Name:            mName.String,
			BusinessType:    mBusinessType.String,
			Industry:        mIndustry.String,
			YearsInBusiness: int(mYearsInBusiness.Int32),
			OwnerName:       mOwnerName.String,
			KYCStatus:       mKycStatus.String,
			CreatedAt:       mCreatedAt.Time,
			UpdatedAt:       mUpdatedAt.Time,
		}
	}

	return &user, nil
}
