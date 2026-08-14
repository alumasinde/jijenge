package Repositories

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Admin/Models"
	"sync"
	"time"
)

var (
	ErrInvalidAction   = errors.New("invalid admin action")
	ErrNotFound        = errors.New("admin action not found")
	ErrAlreadyResolved = errors.New("admin action already resolved")
	ErrSelfApproval    = errors.New("requester cannot approve own action")
)

type Repository interface {
	CreateRequest(context.Context, *Models.ActionRequest) error
	GetRequest(context.Context, uint64) (*Models.ActionRequest, error)
	ApproveAndExecute(context.Context, uint64, uint64, time.Time) error
	Reject(context.Context, uint64, uint64, time.Time) error
}
type MemoryRepository struct {
	mu            sync.Mutex
	next          uint64
	items         map[uint64]*Models.ActionRequest
	userStatus    map[uint64]string
	accountStatus map[uint64]string
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{next: 1, items: map[uint64]*Models.ActionRequest{}, userStatus: map[uint64]string{}, accountStatus: map[uint64]string{}}
}
func cp(x *Models.ActionRequest) *Models.ActionRequest { y := *x; return &y }
func (r *MemoryRepository) CreateRequest(ctx context.Context, x *Models.ActionRequest) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if x == nil || x.TargetID == 0 || x.RequestedBy == 0 {
		return ErrInvalidAction
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	x.ID = r.next
	r.next++
	x.Status = "pending"
	r.items[x.ID] = cp(x)
	return nil
}
func (r *MemoryRepository) GetRequest(ctx context.Context, id uint64) (*Models.ActionRequest, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	x, ok := r.items[id]
	if !ok {
		return nil, ErrNotFound
	}
	return cp(x), nil
}
func (r *MemoryRepository) ApproveAndExecute(ctx context.Context, id, admin uint64, at time.Time) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	x, ok := r.items[id]
	if !ok {
		return ErrNotFound
	}
	if x.Status != "pending" {
		return ErrAlreadyResolved
	}
	if x.RequestedBy == admin {
		return ErrSelfApproval
	}
	x.Status = "approved"
	x.ApprovedBy = &admin
	x.ApprovedAt = &at
	switch x.Action {
	case Models.BlockUser:
		r.userStatus[x.TargetID] = "blocked"
	case Models.UnblockUser:
		r.userStatus[x.TargetID] = "active"
	case Models.FreezeAccount:
		r.accountStatus[x.TargetID] = "frozen"
	case Models.UnfreezeAccount:
		r.accountStatus[x.TargetID] = "active"
	default:
		return ErrInvalidAction
	}
	return nil
}
func (r *MemoryRepository) Reject(ctx context.Context, id, admin uint64, at time.Time) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	x, ok := r.items[id]
	if !ok {
		return ErrNotFound
	}
	if x.Status != "pending" {
		return ErrAlreadyResolved
	}
	if x.RequestedBy == admin {
		return ErrSelfApproval
	}
	x.Status = "rejected"
	x.ApprovedBy = &admin
	x.ApprovedAt = &at
	return nil
}
