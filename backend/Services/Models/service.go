package Models

import "time"

type ServiceStatus string

const (
	ServiceDraft  ServiceStatus = "draft"
	ServiceActive ServiceStatus = "active"
	ServicePaused ServiceStatus = "paused"
)

type Service struct {
	ID                           uint64
	PublicID                     string
	ProviderUserID               uint64
	CategoryID                   uint64
	Title, Description, Currency string
	StartingPriceCents           int64
	Status                       ServiceStatus
	CreatedAt, UpdatedAt         time.Time
}
type Category struct {
	ID         uint64
	Name, Slug string
	ParentID   *uint64
}
