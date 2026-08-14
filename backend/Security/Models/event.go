package Models

import "time"

type Event struct {
	ID        uint64
	PublicID  string
	UserID    *uint64
	EventType string
	RequestID string
	IPAddress string
	UserAgent string
	Metadata  string
	CreatedAt time.Time
}
