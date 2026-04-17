package config

import (
	"log/slog"
	"os"
	"time"

	"github.com/joho/godotenv"
)

type Config struct {
	ServerPort       string
	AgentURL         string
	RedisAddr        string
	KafkaAddr        string
	PostgresAddr     string
	PostgresUser     string
	PostgresPassword string
	PostgresDB       string
	OnnxLibPath      string
	OnnxModelPath    string

	ServerStartupTimeout  time.Duration
	ServerReadTimeout     time.Duration
	ServerWriteTimeout    time.Duration
	ServerIdleTimeout     time.Duration
	ServerShutdownTimeout time.Duration

	RedisPoolSize     int
	RedisMinIdleConns int
	RedisTimeout      time.Duration

	DBMaxOpenConns    int
	DBMaxIdleConns    int
	DBConnMaxLifetime time.Duration
	DBTimeout         time.Duration

	KafkaTopic             string
	KafkaGroupID           string
	KafkaNumPartitions     int
	KafkaReplicationFactor int
	KafkaConsumerMinBytes  int
	KafkaConsumerMaxBytes  int
	KafkaTimeout           time.Duration
	KafkaCommitTimeout     time.Duration

	LoanModelInputName    string
	LoanModelOutputName   string
	LoanFeatureCount      int
	LoanOutputClass       int
	LoanPDIndex           int
	LoanMaxScore          int
	LoanVeryHighThreshold float64
	LoanHighThreshold     float64
	LoanMediumThreshold   float64
	LoanLowThreshold      float64

	AgentTimeout time.Duration

	JWTSecret     string
	JWTExpiration time.Duration
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}

	return fallback
}

func LoadConfig() *Config {
	if err := godotenv.Load(".env"); err != nil {
		slog.Warn(
			"Env file load failed",
			"layer", "CONFIG",
			"error", err.Error(),
		)
	} else {
		slog.Info(
			"Env file loaded successfully",
			"layer", "CONFIG",
			"path", ".env",
		)
	}

	cfg := &Config{
		ServerPort:       getEnv("SERVER_PORT", ":8080"),
		AgentURL:         getEnv("AGENT_URL", "http://localhost:8000/risk-review/report-text"),
		RedisAddr:        getEnv("REDIS_ADDR", "localhost:6379"),
		KafkaAddr:        getEnv("KAFKA_ADDR", "localhost:9092"),
		PostgresAddr:     getEnv("POSTGRES_ADDR", "localhost:5432"),
		PostgresUser:     os.Getenv("POSTGRES_USER"),
		PostgresPassword: os.Getenv("POSTGRES_PASSWORD"),
		PostgresDB:       getEnv("POSTGRES_DB", "solmate_db"),
		OnnxLibPath:      getEnv("ONNX_LIB_PATH", "./ai_models/onnxruntime.dll"),
		OnnxModelPath:    getEnv("ONNX_MODEL_PATH", "./ai_models/XGBoost.onnx"),

		ServerStartupTimeout:  ServerStartupTimeout,
		ServerReadTimeout:     ServerReadTimeout,
		ServerWriteTimeout:    ServerWriteTimeout,
		ServerIdleTimeout:     ServerIdleTimeout,
		ServerShutdownTimeout: ServerShutdownTimeout,

		RedisPoolSize:     RedisPoolSize,
		RedisMinIdleConns: RedisMinIdleConns,
		RedisTimeout:      RedisTimeout,

		DBMaxOpenConns:    DBMaxOpenConns,
		DBMaxIdleConns:    DBMaxIdleConns,
		DBConnMaxLifetime: DBConnMaxLifetime,
		DBTimeout:         DBTimeout,

		KafkaTopic:             KafkaTopic,
		KafkaGroupID:           KafkaGroupID,
		KafkaNumPartitions:     KafkaNumPartitions,
		KafkaReplicationFactor: KafkaReplicationFactor,
		KafkaConsumerMinBytes:  KafkaConsumerMinBytes,
		KafkaConsumerMaxBytes:  KafkaConsumerMaxBytes,
		KafkaTimeout:           KafkaTimeout,
		KafkaCommitTimeout:     KafkaCommitTimeout,

		LoanModelInputName:    LoanModelInputName,
		LoanModelOutputName:   LoanModelOutputName,
		LoanFeatureCount:      LoanFeatureCount,
		LoanOutputClass:       LoanOutputClass,
		LoanPDIndex:           LoanPDIndex,
		LoanMaxScore:          LoanMaxScore,
		LoanVeryHighThreshold: LoanVeryHighThreshold,
		LoanHighThreshold:     LoanHighThreshold,
		LoanMediumThreshold:   LoanMediumThreshold,
		LoanLowThreshold:      LoanLowThreshold,

		AgentTimeout: AgentTimeout,

		JWTSecret:     getEnv("JWT_SECRET", "super-secret-solmate-key"),
		JWTExpiration: 24 * time.Hour,
	}

	slog.Info(
		"Config loaded successfully",
		"layer", "CONFIG",
		"server_port", cfg.ServerPort,
		"redis_addr", cfg.RedisAddr,
		"kafka_addr", cfg.KafkaAddr,
		"pg_addr", cfg.PostgresAddr,
	)

	return cfg
}

func (c *Config) ToRedisConfig() RedisConfig {
	return RedisConfig{
		Addr:     c.RedisAddr,
		PoolSize: c.RedisPoolSize,
		MinIdle:  c.RedisMinIdleConns,
	}
}

func (c *Config) ToDBConfig() DBConfig {
	return DBConfig{
		Addr:        c.PostgresAddr,
		User:        c.PostgresUser,
		Password:    c.PostgresPassword,
		DBName:      c.PostgresDB,
		MaxOpen:     c.DBMaxOpenConns,
		MaxIdle:     c.DBMaxIdleConns,
		MaxLifetime: c.DBConnMaxLifetime,
	}
}

func (c *Config) ToKafkaTopicConfig() KafkaTopicConfig {
	return KafkaTopicConfig{
		Brokers:           []string{c.KafkaAddr},
		Topic:             c.KafkaTopic,
		GroupID:           c.KafkaGroupID,
		Partitions:        c.KafkaNumPartitions,
		ReplicationFactor: c.KafkaReplicationFactor,
		Timeout:           c.KafkaTimeout,
	}
}

func (c *Config) ToConsumerConfig() ConsumerConfig {
	return ConsumerConfig{
		TopicConfig:   c.ToKafkaTopicConfig(),
		MinBytes:      c.KafkaConsumerMinBytes,
		MaxBytes:      c.KafkaConsumerMaxBytes,
		CommitTimeout: c.KafkaCommitTimeout,
	}
}

func (c *Config) ToPOSServiceConfig() POSServiceConfig {
	return POSServiceConfig{
		DBTimeout:    c.DBTimeout,
		RedisTimeout: c.RedisTimeout,
	}
}

func (c *Config) ToLoanServiceConfig() LoanServiceConfig {
	return LoanServiceConfig{
		ModelInputName:    c.LoanModelInputName,
		ModelOutputName:   c.LoanModelOutputName,
		FeatureCount:      c.LoanFeatureCount,
		OutputClass:       c.LoanOutputClass,
		PDIndex:           c.LoanPDIndex,
		MaxScore:          c.LoanMaxScore,
		VeryHighThreshold: c.LoanVeryHighThreshold,
		HighThreshold:     c.LoanHighThreshold,
		MediumThreshold:   c.LoanMediumThreshold,
		LowThreshold:      c.LoanLowThreshold,
		DBTimeout:         c.DBTimeout,
		RedisTimeout:      c.RedisTimeout,
	}
}

func (c *Config) ToAgentServiceConfig() AgentServiceConfig {
	return AgentServiceConfig{
		AgentURL: c.AgentURL,
		Timeout:  c.AgentTimeout,
	}
}
func (c *Config) ToAuthServiceConfig() AuthServiceConfig {
	return AuthServiceConfig{
		JWTSecret:     c.JWTSecret,
		JWTExpiration: c.JWTExpiration,
		DBTimeout:     c.DBTimeout,
	}
}
