package models

import "time"

type Merchant struct {
	ID              string    `json:"id"`
	Name            string    `json:"name"`
	BusinessType    string    `json:"business_type"`
	Industry        string    `json:"industry"`
	YearsInBusiness int       `json:"years_in_business"`
	OwnerName       string    `json:"owner_name"`
	KYCStatus       string    `json:"kyc_status"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}
