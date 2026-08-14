package Models

import "time"

type User struct {
	ID           uint64
	PublicID     string
	Email        string
	PasswordHash string
	Status       string
	CreatedAt    time.Time
	UpdatedAt    time.Time
}

const (
	StatusActive  = "active"
	StatusPending = "pending"
	StatusBlocked = "blocked"
	StatusDeleted = "deleted"
)
