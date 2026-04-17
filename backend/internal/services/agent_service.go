package services

import (
	"backend/internal/config"
	"backend/internal/infrastructure"
	"backend/internal/models"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
)

type AgentService struct {
	httpClient *http.Client
	cfg        config.AgentServiceConfig
	log        *slog.Logger
}

func NewAgentService(cfg config.AgentServiceConfig) *AgentService {
	logger := infrastructure.GetLogger("AGENT_SERVICE")

	return &AgentService{
		httpClient: &http.Client{},
		cfg:        cfg,
		log:        logger,
	}
}

func (s *AgentService) ReviewRisk(ctx context.Context, reqData models.AgentRiskRequest) (*models.AgentRiskResponse, error) {
	s.log.Debug(
		"Agent review started",
		"customer_id", reqData.EnterpriseCICMetrics.CustomerID,
		"urls_count", len(s.cfg.AgentURLs),
	)

	jsonData, err := json.Marshal(reqData)
	if err != nil {
		s.log.Error(
			"Marshal request data failed",
			"customer_id", reqData.EnterpriseCICMetrics.CustomerID,
			infrastructure.KeyError, err.Error(),
		)
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	var lastErr error

	for i, agentURL := range s.cfg.AgentURLs {
		res, err := s.callAgent(ctx, agentURL, jsonData, reqData.EnterpriseCICMetrics.CustomerID)
		if err != nil {
			s.log.Warn(
				"Agent URL failed, trying next",
				"customer_id", reqData.EnterpriseCICMetrics.CustomerID,
				"url_index", i,
				"url", agentURL,
				infrastructure.KeyError, err.Error(),
			)
			lastErr = err
			continue
		}

		s.log.Info(
			"Agent review completed successfully",
			"customer_id", reqData.EnterpriseCICMetrics.CustomerID,
			"url_index", i,
			"url", agentURL,
		)
		return res, nil
	}

	s.log.Error(
		"All agent URLs exhausted",
		"customer_id", reqData.EnterpriseCICMetrics.CustomerID,
		"urls_tried", len(s.cfg.AgentURLs),
		infrastructure.KeyError, lastErr.Error(),
	)
	return nil, fmt.Errorf("all agent URLs failed, last error: %w", lastErr)
}

func (s *AgentService) callAgent(ctx context.Context, agentURL string, jsonData []byte, customerID string) (*models.AgentRiskResponse, error) {
	reqCtx, reqCancel := context.WithTimeout(ctx, s.cfg.Timeout)
	defer reqCancel()

	req, err := http.NewRequestWithContext(reqCtx, http.MethodPost, agentURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	res, err := s.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("execute request: %w", err)
	}
	defer res.Body.Close()

	if res.StatusCode < 200 || res.StatusCode >= 300 {
		return nil, fmt.Errorf("unexpected status code: %d", res.StatusCode)
	}

	bodyBytes, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, fmt.Errorf("read response body: %w", err)
	}

	var agentRes models.AgentRiskResponse
	if err := json.Unmarshal(bodyBytes, &agentRes); err != nil {
		return nil, fmt.Errorf("unmarshal response: %w", err)
	}

	return &agentRes, nil
}
