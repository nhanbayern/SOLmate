package infrastructure

import (
	"backend/internal/config"
	"context"
	"fmt"

	"github.com/redis/go-redis/v9"
)

func ConnectRedis(ctx context.Context, cfg config.RedisConfig) (*redis.Client, error) {
	logger := GetLogger("INFRA_REDIS")

	client := redis.NewClient(&redis.Options{
		Addr:         cfg.Addr,
		PoolSize:     cfg.PoolSize,
		MinIdleConns: cfg.MinIdle,
	})
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("ping redis: %w", err)
	}

	logger.Info(
		"Redis connected successfully",
		"addr", cfg.Addr,
	)

	return client, nil
}
