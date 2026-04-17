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
	"time"

	_ "backend/docs"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
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
	userRepo := repositories.NewUserRepo(pgDB)
	redisRepo := repositories.NewRedisRepo(rdb)
	agentService := services.NewAgentService(cfg.ToAgentServiceConfig())
	authService := services.NewAuthService(userRepo, cfg.ToAuthServiceConfig())
	dashboardService := services.NewDashboardService(pgRepo, cfg.ToLoanServiceConfig())

	loanService, err := services.NewLoanService(
		pgRepo,
		redisRepo,
		agentService,
		cfg.ToLoanServiceConfig(),
		cfg.OnnxLibPath,
		cfg.OnnxModelPath,
	)
	if err != nil {
		return fmt.Errorf("init loan service: %w", err)
	}
	closer.Add(loanService.Close)

	httpHandler := handlers.NewHTTPHandler(loanService)
	sseHandler := handlers.NewSSEHandler(rdb)
	authHandler := handlers.NewAuthHandler(authService)

	merchantHandler := handlers.NewMerchantHandler(dashboardService)
	loanDashboardHandler := handlers.NewLoanHandler(dashboardService)
	transactionHandler := handlers.NewTransactionHandler(dashboardService)
	statsHandler := handlers.NewStatsHandler(dashboardService)
	customerHandler := handlers.NewCustomerHandler(dashboardService)

	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	// CORS configuration to allow frontend dev server (port 5173)
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:5173"},
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))
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

	auth := r.Group("/api/auth")
	{
		auth.POST("/login", authHandler.Login)
		auth.GET("/me", authHandler.AuthMiddleware(), authHandler.Me)
	}

	api := r.Group("/api")
	api.Use(authHandler.AuthMiddleware())
	{
		api.POST("/loans/evaluate", httpHandler.EvaluateLoan)

		api.GET("/merchants", merchantHandler.List)
		api.GET("/merchants/:id", merchantHandler.Get)

		api.GET("/loans", loanDashboardHandler.List)
		api.GET("/loans/:id", loanDashboardHandler.Get)
		api.POST("/loans/:id/decision", loanDashboardHandler.Decision)

		api.GET("/transactions", transactionHandler.List)

		api.GET("/stats", statsHandler.Get)

		api.GET("/loans/stream", sseHandler.SubscribeToMerchantStatus)

		customer := api.Group("/customer")
		{
			customer.GET("/loans", customerHandler.ListLoans)
			customer.POST("/loans", customerHandler.RequestLoan)
		}
	}

	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

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

// @title           SOLmate Banker Dashboard API
// @version         1.0
// @description     Backend APIs for SOLmate - AI-powered lending platform.
// @host            localhost:8080
// @BasePath        /
// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization
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
