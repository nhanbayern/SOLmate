package events

import (
	"backend/internal/config"
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"strconv"

	"github.com/segmentio/kafka-go"
)

type POSService interface {
	ProcessTransaction(ctx context.Context, log *models.TransactionLog) error
}

type KafkaConsumer struct {
	reader     *kafka.Reader
	posService POSService
	cfg        config.ConsumerConfig
	log        *slog.Logger
}

func ensureTopicExists(logger *slog.Logger, cfg config.KafkaTopicConfig) error {
	dialer := &kafka.Dialer{
		Timeout:   cfg.Timeout,
		DualStack: true,
	}

	conn, err := dialer.Dial("tcp", cfg.Brokers[0])
	if err != nil {
		return fmt.Errorf("dial initial broker: %w", err)
	}
	defer conn.Close()

	topicPartitions, err := conn.ReadPartitions()
	if err != nil {
		return fmt.Errorf("read partitions: %w", err)
	}

	for _, p := range topicPartitions {
		if p.Topic == cfg.Topic {
			logger.Info(
				"Topic already exists",
				"topic", cfg.Topic,
			)

			return nil
		}
	}

	controller, err := conn.Controller()
	if err != nil {
		return fmt.Errorf("get controller: %w", err)
	}

	controllerAddr := net.JoinHostPort(controller.Host, strconv.Itoa(controller.Port))
	controllerConn, err := dialer.Dial("tcp", controllerAddr)
	if err != nil {
		return fmt.Errorf("dial controller: %w", err)
	}
	defer controllerConn.Close()

	topicConfig := kafka.TopicConfig{
		Topic:             cfg.Topic,
		NumPartitions:     cfg.Partitions,
		ReplicationFactor: cfg.ReplicationFactor,
	}

	if err := controllerConn.CreateTopics(topicConfig); err != nil {
		return fmt.Errorf("create topic: %w", err)
	}

	logger.Info(
		"Topic created successfully",
		"topic", cfg.Topic,
		"num_partitions", topicConfig.NumPartitions,
	)

	return nil
}

func NewKafkaConsumer(ctx context.Context, posService POSService, cfg config.ConsumerConfig) (*KafkaConsumer, error) {
	logger := infrastructure.GetLogger("KAFKA_CONSUMER")

	if err := ensureTopicExists(logger, cfg.TopicConfig); err != nil {
		return nil, fmt.Errorf("setup kafka brokers: %w", err)
	}

	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers:     cfg.TopicConfig.Brokers,
		Topic:       cfg.TopicConfig.Topic,
		GroupID:     cfg.TopicConfig.GroupID,
		MinBytes:    cfg.MinBytes,
		MaxBytes:    cfg.MaxBytes,
		StartOffset: kafka.FirstOffset,
	})

	logger.Info(
		"Connection warming up",
		"topic", cfg.TopicConfig.Topic,
	)

	if conn, err := kafka.DialLeader(ctx, "tcp", cfg.TopicConfig.Brokers[0], cfg.TopicConfig.Topic, 0); err != nil {
		logger.Warn(
			"Warm-up connection failed",
			infrastructure.KeyError, err.Error(),
		)
	} else {
		conn.Close()

		logger.Info(
			"Warm-up connection completed successfully",
		)
	}

	logger.Info(
		"Consumer initialized successfully",
		"brokers", cfg.TopicConfig.Brokers,
		"topic", cfg.TopicConfig.Topic,
		"group_id", cfg.TopicConfig.GroupID,
	)

	return &KafkaConsumer{
		reader:     r,
		posService: posService,
		cfg:        cfg,
		log:        logger,
	}, nil
}

func (c *KafkaConsumer) ConsumeTransactionLog(ctx context.Context) error {
	for {
		msg, err := c.reader.FetchMessage(ctx)
		if err != nil {
			if errors.Is(err, context.Canceled) || ctx.Err() != nil {
				c.log.Info("Context cancelled")
				return nil
			}
			return fmt.Errorf("read message: %w", err)
		}

		var log models.TransactionLog
		if err := json.Unmarshal(msg.Value, &log); err != nil {
			c.log.Error(
				"Transaction unmarshal failed",
				"kafka_key", string(msg.Key),
				infrastructure.KeyError, err.Error(),
			)

			c.reader.CommitMessages(ctx, msg)
			continue
		}

		c.log.Info(
			"Transaction consumed successfully",
			"id", log.ID,
			"merchant_id", log.MerchantID,
			"customer_id", log.CustomerID,
			"amount", log.Amount,
			"is_refund", log.IsRefund,
			"pos_terminal_id", log.POSTerminalID,
		)

		if err := c.posService.ProcessTransaction(ctx, &log); err != nil {
			return fmt.Errorf("process transaction: %w", err)
		}

		commitCtx, commitCancel := context.WithTimeout(ctx, c.cfg.CommitTimeout)
		if err := c.reader.CommitMessages(commitCtx, msg); err != nil {
			c.log.Error(
				"Message commit failed",
				"id", log.ID,
				"merchant_id", log.MerchantID,
				"amount", log.Amount,
				"is_refund", log.IsRefund,
				"pos_terminal_id", log.POSTerminalID,
				infrastructure.KeyError, err.Error(),
			)
		}

		commitCancel()
	}
}

func (c *KafkaConsumer) Close() error {
	if err := c.reader.Close(); err != nil {
		return fmt.Errorf("close consumer: %w", err)
	}

	return nil
}
