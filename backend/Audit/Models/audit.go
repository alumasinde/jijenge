package Models

import "time"

type AuditEvent struct {
	ID           uint64
	PublicID     string
	ActorUserID  *uint64
	Action       string
	ResourceType string
	ResourceID   string
	RequestID    string
	IPAddress    string
	UserAgent    string
	Outcome      string
	Reason       string
	Metadata     string
	CreatedAt    time.Time
	PreviousHash string
	EventHash    string
}

type ReconciliationRun struct {
	ID                  uint64
	PublicID            string
	Status              string
	AccountsChecked     int64
	TransactionsChecked int64
	Discrepancies       int64
	StartedAt           time.Time
	FinishedAt          *time.Time
}

type ReconciliationIssue struct {
	ID            uint64
	RunID         uint64
	IssueType     string
	AccountID     *uint64
	TransactionID *uint64
	ExpectedCents int64
	ActualCents   int64
	Details       string
	CreatedAt     time.Time
}
