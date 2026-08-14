package Models

import "time"

type AccountStatus string

const (
	AccountActive AccountStatus = "active"
	AccountFrozen AccountStatus = "frozen"
	AccountClosed AccountStatus = "closed"
)

type Account struct {
	ID          uint64
	PublicID    string
	OwnerUserID *uint64
	Currency    string
	Status      AccountStatus
	CreatedAt   time.Time
}

type Entry struct {
	AccountID   uint64
	DebitCents  int64
	CreditCents int64
}

type Transaction struct {
	ID             uint64
	PublicID       string
	IdempotencyKey string
	Currency       string
	Description    string
	CreatedAt      time.Time
	Entries        []Entry
}

type Balance struct {
	AccountID      uint64
	Currency       string
	AvailableCents int64
	HeldCents      int64
}

type HoldStatus string

const (
	HoldActive    HoldStatus = "active"
	HoldReleased  HoldStatus = "released"
	HoldCaptured  HoldStatus = "captured"
	HoldCancelled HoldStatus = "cancelled"
)

type Hold struct {
	ID          uint64
	PublicID    string
	AccountID   uint64
	Reference   string
	AmountCents int64
	Status      HoldStatus
	CreatedAt   time.Time
	UpdatedAt   time.Time
}
