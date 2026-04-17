package repositories

import (
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"github.com/redis/go-redis/v9"
)

type RedisRepo struct {
	rdb *redis.Client
	log *slog.Logger
}

func NewRedisRepo(rdb *redis.Client) *RedisRepo {
	logger := infrastructure.GetLogger("REDIS_REPO")

	return &RedisRepo{
		rdb: rdb,
		log: logger,
	}
}

func (r *RedisRepo) UpdateFeatures(ctx context.Context, features *models.MerchantFeatures) error {
	key := fmt.Sprintf("merchant:%s:customer:%s:features", features.MerchantID, features.CustomerID)

	result, err := json.Marshal(features.Features)
	if err != nil {
		return fmt.Errorf("marshal features: %w", err)
	}

	if err := r.rdb.Set(ctx, key, result, 0).Err(); err != nil {
		return fmt.Errorf("update features: %w", err)
	}

	r.log.Debug(
		"Features updated successfully",
		"merchant_id", features.MerchantID,
		"customer_id", features.CustomerID,
	)

	return nil
}

func (r *RedisRepo) GetFeatures(ctx context.Context, merchantID, customerID string) (*models.MerchantFeatures, error) {
	key := fmt.Sprintf("merchant:%s:customer:%s:features", merchantID, customerID)

	result, err := r.rdb.Get(ctx, key).Bytes()
	if err != nil {
		if err == redis.Nil {
			return nil, fmt.Errorf("get features: %w", err)
		}

		return nil, fmt.Errorf("read redis: %w", err)
	}

	var featuresArr []float64
	if err := json.Unmarshal(result, &featuresArr); err != nil {
		return nil, fmt.Errorf("unmarshal data: %w", err)
	}

	r.log.Debug(
		"Features retrieved successfully",
		"merchant_id", merchantID,
		"customer_id", customerID,
	)

	return &models.MerchantFeatures{
		MerchantID: merchantID,
		CustomerID: customerID,
		Features:   featuresArr,
	}, nil
}

func (r *RedisRepo) PublishUpdate(ctx context.Context, merchantID string, message string) error {
	channel := fmt.Sprintf("sse:merchant:%s", merchantID)

	if err := r.rdb.Publish(ctx, channel, message).Err(); err != nil {
		return fmt.Errorf("publish update: %w", err)
	}

	r.log.Debug(
		"Published update to Redis Pub/Sub successfully",
		"merchant_id", merchantID,
		"channel", channel,
	)

	return nil
}
