package Models

import "time"

type AssignmentStatus string

const (
	AssignmentAssigned  AssignmentStatus = "assigned"
	AssignmentSubmitted AssignmentStatus = "submitted"
	AssignmentVerified  AssignmentStatus = "verified"
	AssignmentRejected  AssignmentStatus = "rejected"
	AssignmentCancelled AssignmentStatus = "cancelled"
)

type Assignment struct {
	ID            uint64
	TaskID        uint64
	ApplicationID uint64
	WorkerID      uint64
	AssignedBy    uint64
	Status        AssignmentStatus
	SubmittedAt   *time.Time
	VerifiedAt    *time.Time
	CreatedAt     time.Time
	UpdatedAt     time.Time
}
