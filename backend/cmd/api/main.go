package main

import (
	"backend/internal/config"
	"backend/internal/handlers"
	"backend/internal/infrastructure"
	"backend/internal/repositories"
	"backend/internal/services"
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/gin-gonic/gin"
)

func run() error {
	infrastructure.InitLogger()
	logger := infrastructure.GetLogger("MAIN")
	closer := infrastructure.NewAppCloser(logger)

	cfg := config.LoadConfig()

	startupCtx, startupCancel := context.WithTimeout(context.Background(), cfg.ServerStartupTimeout)
	defer startupCancel()

	pgDB, err := infrastructure.ConnectPostgres(startupCtx, cfg.ToDBConfig())
	if err != nil {
		return fmt.Errorf("connect postgres: %w", err)
	}
	closer.Add(pgDB.Close)

	rdb, err := infrastructure.ConnectRedis(startupCtx, cfg.ToRedisConfig())
	if err != nil {
		return fmt.Errorf("connect redis: %w", err)
	}
	closer.Add(rdb.Close)

	pgRepo := repositories.NewPostgresRepo(pgDB)
	redisRepo := repositories.NewRedisRepo(rdb)
	agentService := services.NewAgentService(cfg.ToAgentServiceConfig())

	dllPath := "./ai_models/onnxruntime.dll"
	modelPath := "./ai_models/XGBoost.onnx"
	loanService, err := services.NewLoanService(pgRepo, redisRepo, agentService, cfg.ToLoanServiceConfig(), dllPath, modelPath)
	if err != nil {
		return fmt.Errorf("init loan service: %w", err)
	}
	closer.Add(loanService.Close)

	httpHandler := handlers.NewHTTPHandler(loanService)
	sseHandler := handlers.NewSSEHandler(rdb)

	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())

	err = r.SetTrustedProxies([]string{
		"10.0.0.0/8",
		"172.16.0.0/12",
		"192.168.0.0/16",
		"127.0.0.0/8",
		"::1",
	})
	if err != nil {
		return fmt.Errorf("set trusted proxies: %w", err)
	}

	r.GET("/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "pong",
			"status":  "success",
		})
	})

	r.POST("api/loans/evaluate", httpHandler.EvaluateLoan)
	r.GET("api/loans/stream", sseHandler.SubscribeToMerchantStatus)

	srv := &http.Server{
		Addr:         cfg.ServerPort,
		Handler:      r,
		ReadTimeout:  cfg.ServerReadTimeout,
		WriteTimeout: cfg.ServerWriteTimeout,
		IdleTimeout:  cfg.ServerIdleTimeout,
	}

	srvErrChan := make(chan error, 1)

	go func() {
		logger.Info(
			"Server started",
			"url", fmt.Sprintf("http://localhost%s", cfg.ServerPort),
		)

		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error(
				"HTTP server crashed",
				infrastructure.KeyAction, "run_http_server",
				infrastructure.KeyStatus, infrastructure.StatusFailed,
				infrastructure.KeyError, err.Error(),
			)

			srvErrChan <- err
		}
	}()

	signalCtx, signalCancel := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer signalCancel()

	select {
	case err := <-srvErrChan:
		return fmt.Errorf("run server: %w", err)
	case <-signalCtx.Done():
		logger.Info(
			"Shutdown signal received",
			"signal", "SIGINT/SIGTERM",
		)
	}

	logger.Info("Server shutdown started")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), cfg.ServerShutdownTimeout)
	defer shutdownCancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		return fmt.Errorf("shutdown server: %w", err)
	}

	closer.CloseAll()

	logger.Info("Server exited")

	return nil
}

func main() {
	if err := run(); err != nil {
		slog.Error(
			"Application startup failed",
			"layer", "MAIN",
			infrastructure.KeyAction, "run_application",
			infrastructure.KeyStatus, infrastructure.StatusFailed,
			infrastructure.KeyError, err.Error(),
		)

		os.Exit(1)
	}
}
