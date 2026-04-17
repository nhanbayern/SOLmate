package config

import "time"

const (
	ServerStartupTimeout  = 5 * time.Second
	ServerReadTimeout     = 5 * time.Second
	ServerWriteTimeout    = 15 * time.Second
	ServerIdleTimeout     = 15 * time.Second
	ServerShutdownTimeout = 5 * time.Second
)

const (
	RedisPoolSize     = 1000
	RedisMinIdleConns = 200
	RedisTimeout      = 500 * time.Millisecond
)

const (
	DBMaxOpenConns    = 200
	DBMaxIdleConns    = 50
	DBConnMaxLifetime = 5 * time.Minute
	DBTimeout         = 5 * time.Second
)

const (
	KafkaTopic             = "transaction"
	KafkaGroupID           = "solmate_worker_group"
	KafkaNumPartitions     = 3
	KafkaReplicationFactor = 1
	KafkaConsumerMinBytes  = 10e3
	KafkaConsumerMaxBytes  = 10e6
	KafkaTimeout           = 5 * time.Second
	KafkaCommitTimeout     = 2 * time.Second
)

const (
	LoanModelInputName    = "float_input"
	LoanModelOutputName   = "variable"
	LoanFeatureCount      = 12
	LoanOutputClass       = 1
	LoanPDIndex           = 0
	LoanMaxScore          = 1000
	LoanVeryGoodThreshold = 0.1
	LoanGoodThreshold     = 0.3
	LoanMediumThreshold   = 0.5
	LoanPoorThreshold     = 0.7
)

const (
	AgentTimeout = 15 * time.Second
)
