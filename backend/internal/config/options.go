package config

import "time"

type RedisConfig struct {
	Addr     string
	PoolSize int
	MinIdle  int
}

type DBConfig struct {
	Addr        string
	User        string
	Password    string
	DBName      string
	MaxOpen     int
	MaxIdle     int
	MaxLifetime time.Duration
}

type KafkaTopicConfig struct {
	Brokers           []string
	Topic             string
	GroupID           string
	Partitions        int
	ReplicationFactor int
	Timeout           time.Duration
}

type ConsumerConfig struct {
	TopicConfig   KafkaTopicConfig
	MinBytes      int
	MaxBytes      int
	CommitTimeout time.Duration
}

type POSServiceConfig struct {
	DBTimeout    time.Duration
	RedisTimeout time.Duration
}

type LoanServiceConfig struct {
	ModelInputName    string
	ModelOutputName   string
	FeatureCount      int
	OutputClass       int
	PDIndex           int
	MaxScore          int
	VeryGoodThreshold float64
	GoodThreshold     float64
	MediumThreshold   float64
	PoorThreshold     float64
	DBTimeout         time.Duration
	RedisTimeout      time.Duration
}

type AgentServiceConfig struct {
	AgentURL string
	Timeout  time.Duration
}

type AuthServiceConfig struct {
	JWTSecret     string
	JWTExpiration time.Duration
	DBTimeout     time.Duration
}
