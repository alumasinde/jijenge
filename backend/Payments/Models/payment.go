package Models

import "time"

type PaymentStatus string

const (
	StatusPending   PaymentStatus = "pending"
	StatusConfirmed PaymentStatus = "confirmed"
	StatusFailed    PaymentStatus = "failed"
	StatusCancelled PaymentStatus = "cancelled"
)

type Payment struct {
	ID              uint64
	PublicID        string
	Provider        string
	ProviderRef     string
	ProviderEventID string
	AccountID       uint64
	AmountCents     int64
	Currency        string
	Status          PaymentStatus
	CreatedAt       time.Time
	UpdatedAt       time.Time
}

type WebhookEvent struct {
	ID          uint64
	Provider    string
	EventID     string
	PaymentRef  string
	AmountCents int64
	Currency    string
	Signature   string
	PayloadHash [32]byte
	Processed   bool
	CreatedAt   time.Time
	ProcessedAt *time.Time
}
