package Models

import "time"

type TaskStatus string

const (
	StatusDraft      TaskStatus = "draft"
	StatusPublished  TaskStatus = "published"
	StatusInProgress TaskStatus = "in_progress"
	StatusCompleted  TaskStatus = "completed"
	StatusCancelled  TaskStatus = "cancelled"
)

type Task struct {
	ID          uint64
	PublicID    string
	OwnerUserID uint64
	CategoryID  uint64
	Title       string
	Description string
	BudgetCents int64
	Currency    string
	Status      TaskStatus
	CreatedAt   time.Time
	UpdatedAt   time.Time
}
