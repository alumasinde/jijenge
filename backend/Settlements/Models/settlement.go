package Models

import "time"

type Method string

const (
	Platform     Method = "platform"
	Cash         Method = "cash"
	MobileMoney  Method = "mobile_money"
	BankTransfer Method = "bank_transfer"
	Other        Method = "other"
)

type Status string

const (
	Pending   Status = "pending"
	Claimed   Status = "claimed"
	Confirmed Status = "confirmed"
	Disputed  Status = "disputed"
	Cancelled Status = "cancelled"
)

type Settlement struct {
	ID                                                 uint64
	PublicID                                           string
	TaskID, AssignmentID, PayerUserID, PayeeUserID     uint64
	Method                                             Method
	AmountCents                                        int64
	Currency                                           string
	Status                                             Status
	ClaimedBy, ConfirmedBy                             *uint64
	ConfirmedAt                                        *time.Time
	EvidenceReference, ConfirmationNote, DisputeReason string
	IdempotencyKey                                     string
	CreatedAt, UpdatedAt                               time.Time
}
