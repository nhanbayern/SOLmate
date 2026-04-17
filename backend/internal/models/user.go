package models

import "time"

type User struct {
	ID           string    `json:"user_id"`
	Username     string    `json:"username"`
	PasswordHash string    `json:"-"`
	Role         string    `json:"role"`
	MerchantID   *string   `json:"merchant_id"`
	Merchant     *Merchant `json:"merchant,omitempty"`
	CustomerID   *string   `json:"customer_id"`
	Status       string    `json:"status"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
}

type AuthUser struct {
	UserID     string    `json:"user_id"`
	CustomerID *string   `json:"customer_id"`
	MerchantID *string   `json:"merchant_id"`
	Merchant   *Merchant `json:"merchant,omitempty"`
	Role       string    `json:"role"`
	Status     string    `json:"status"`
}
