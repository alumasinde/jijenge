package Models

import "time"

type ActionType string

const (
	BlockUser       ActionType = "block_user"
	UnblockUser     ActionType = "unblock_user"
	FreezeAccount   ActionType = "freeze_account"
	UnfreezeAccount ActionType = "unfreeze_account"
)

type ActionRequest struct {
	ID          uint64
	PublicID    string
	Action      ActionType
	TargetID    uint64
	RequestedBy uint64
	ApprovedBy  *uint64
	Status      string
	Reason      string
	CreatedAt   time.Time
	ApprovedAt  *time.Time
}
