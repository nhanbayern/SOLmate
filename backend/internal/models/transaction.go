package models

import "time"

type TransactionLog struct {
	ID              int       `json:"id"`
	MerchantID      string    `json:"merchant_id"`
	CustomerID      string    `json:"customer_id"`
	Amount          float64   `json:"amount"`
	IsRefund        bool      `json:"is_refund"`
	POSTerminalID   string    `json:"pos_terminal_id"`
	TransactionTime time.Time `json:"transaction_time"`
	CreatedAt       time.Time `json:"created_at"`
}
