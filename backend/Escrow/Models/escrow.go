package Models

import "time"

type Status string

const (
	Funded              Status = "funded"
	Submitted           Status = "submitted"
	VerificationPending Status = "verification_pending"
	Released            Status = "released"
	Refunded            Status = "refunded"
	Disputed            Status = "disputed"
	Cancelled           Status = "cancelled"
)

type Escrow struct {
	ID               uint64
	PublicID         string
	TaskID           uint64
	AssignmentID     uint64
	PayerAccountID   uint64
	WorkerAccountID  uint64
	PayerUserID      uint64
	WorkerUserID     uint64
	AmountCents      int64
	Currency         string
	Status           Status
	CreatedAt        time.Time
	UpdatedAt        time.Time
	ReleasedAt       *time.Time
	PlatformFeeCents int64
	DisputeID        *uint64
	IdempotencyKey   string
}
