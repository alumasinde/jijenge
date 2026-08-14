package Models

import "time"

type Status string

const (
	Unread Status = "unread"
	Read   Status = "read"
)

type Channel string

const (
	InApp Channel = "in_app"
	Email Channel = "email"
	SMS   Channel = "sms"
	Push  Channel = "push"
)

type Notification struct {
	ID            uint64
	PublicID      string
	UserID        uint64
	Channel       Channel
	Title         string
	Body          string
	Type          string
	ReferenceType string
	ReferenceID   string
	Status        Status
	CreatedAt     time.Time
	ReadAt        *time.Time
}
type Preference struct {
	UserID    uint64
	Channel   Channel
	EventType string
	Enabled   bool
	UpdatedAt time.Time
}
