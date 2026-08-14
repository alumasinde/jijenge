package Models

import "time"

type ApplicationStatus string

const (
	ApplicationPending   ApplicationStatus = "pending"
	ApplicationAccepted  ApplicationStatus = "accepted"
	ApplicationRejected  ApplicationStatus = "rejected"
	ApplicationWithdrawn ApplicationStatus = "withdrawn"
)

type Application struct {
	ID            uint64
	TaskID        uint64
	ApplicantID   uint64
	Message       string
	ProposedCents int64
	Status        ApplicationStatus
	CreatedAt     time.Time
	UpdatedAt     time.Time
}
