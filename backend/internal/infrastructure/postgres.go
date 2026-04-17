package infrastructure

import (
	"backend/internal/config"
	"context"
	"database/sql"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"

	_ "github.com/lib/pq"
)

func autoMigrate(ctx context.Context, db *sql.DB, logger *slog.Logger) error {
	schemaPath := filepath.Join("migrations", "init_schema.sql")
	schemaBytes, err := os.ReadFile(schemaPath)
	if err != nil {
		logger.Warn(
			"Schema file found failed",
			"path", schemaPath,
			KeyError, err.Error(),
		)

		return nil
	}

	if _, err = db.ExecContext(ctx, string(schemaBytes)); err != nil {
		return fmt.Errorf("execute schema script: %w", err)
	}

	logger.Info("Database schema initialized successfully")

	return nil
}

func ConnectPostgres(ctx context.Context, cfg config.DBConfig) (*sql.DB, error) {
	logger := GetLogger("INFRA_POSTGRES")

	dsn := fmt.Sprintf("postgres://%s:%s@%s/%s?sslmode=disable", cfg.User, cfg.Password, cfg.Addr, cfg.DBName)

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("open postgres connection: %w", err)
	}

	db.SetMaxOpenConns(cfg.MaxOpen)
	db.SetMaxIdleConns(cfg.MaxIdle)
	db.SetConnMaxLifetime(cfg.MaxLifetime)

	if err := db.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("ping postgres: %w", err)
	}

	logger.Info(
		"Postgres connected successfully",
		"addr", cfg.Addr,
		"db_name", cfg.DBName,
	)

	if err := autoMigrate(ctx, db, logger); err != nil {
		return nil, fmt.Errorf("run auto migration: %w", err)
	}

	return db, nil
}
