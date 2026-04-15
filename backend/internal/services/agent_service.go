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
		"customer_id", reqData.CustomerID,
	)

	reqCtx, reqCancel := context.WithTimeout(ctx, s.cfg.Timeout)
	defer reqCancel()

	jsonData, err := json.Marshal(reqData)
	if err != nil {
		s.log.Error(
			"Marshal request data failed",
			"customer_id", reqData.CustomerID,
			infrastructure.KeyError, err.Error(),
		)
		return nil, fmt.Errorf("marshal request: %w", &err)
	}

	req, err := http.NewRequestWithContext(reqCtx, http.MethodPost, s.cfg.AgentURL, bytes.NewBuffer(jsonData))
	if err != nil {
		s.log.Error(
			"Create http request failed",
			"customer_id", reqData.CustomerID,
			infrastructure.KeyError, err.Error(),
		)
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	res, err := s.httpClient.Do(req)
	if err != nil {
		s.log.Error(
			"Execute http request failed",
			"customer_id", reqData.CustomerID,
			infrastructure.KeyError, err.Error(),
		)
		return nil, fmt.Errorf("execute request: %w", err)
	}
	defer res.Body.Close()

	bodyBytes, err := io.ReadAll(res.Body)
	if err != nil {
		s.log.Error(
			"Read response body failed",
			"customer_id", reqData.CustomerID,
			infrastructure.KeyError, err.Error(),
		)
		return nil, fmt.Errorf("read response body: %w", err)
	}

	var agentRes models.AgentRiskResponse
	if err := json.Unmarshal(bodyBytes, &agentRes); err != nil {
		s.log.Error(
			"Unmarshal agent response failed",
			"customer_id", reqData.CustomerID,
			infrastructure.KeyError, err.Error(),
		)
		return nil, fmt.Errorf("unmarshal response: %w", err)
	}

	s.log.Info(
		"Agent review completed successfully",
		"customer_id", reqData.CustomerID,
		"expected_risk_class", agentRes.ExpectedRiskClass,
	)

	return &agentRes, nil
}
