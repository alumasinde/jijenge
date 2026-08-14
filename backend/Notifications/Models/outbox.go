package Models

import "time"

type OutboxStatus string

const (
	OutboxPending    OutboxStatus = "pending"
	OutboxProcessing OutboxStatus = "processing"
	OutboxSent       OutboxStatus = "sent"
	OutboxFailed     OutboxStatus = "failed"
)

type Outbox struct {
	ID             uint64
	PublicID       string
	NotificationID uint64
	Channel        Channel
	Status         OutboxStatus
	Attempts       int
	AvailableAt    time.Time
	LockedAt       *time.Time
	SentAt         *time.Time
	LastError      string
	CreatedAt      time.Time
	UpdatedAt      time.Time
}
