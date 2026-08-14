package Models

import "time"

type Session struct {
	ID              uint64
	UserID          uint64
	AccessTokenHash [32]byte
	TokenHash       [32]byte
	ExpiresAt       time.Time
	RevokedAt       *time.Time
	CreatedAt       time.Time
	LastSeenAt      *time.Time
}
