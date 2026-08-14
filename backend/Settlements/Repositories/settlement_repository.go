package Repositories

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Settlements/Models"
	"strings"
	"sync"
	"time"
)

var (
	ErrNotFound     = errors.New("settlement not found")
	ErrInvalidState = errors.New("invalid settlement state")
	ErrDuplicate    = errors.New("settlement already exists")
)

type Repository interface {
	Create(context.Context, *Models.Settlement) error
	CreateForUser(context.Context, *Models.Settlement, uint64) error
	Find(context.Context, uint64) (*Models.Settlement, error)
	Claim(context.Context, uint64, uint64, time.Time) error
	Confirm(context.Context, uint64, uint64, time.Time) error
	ConfirmWithNote(context.Context, uint64, uint64, string, time.Time) error
	Dispute(context.Context, uint64, uint64, time.Time) error
	DisputeWithReason(context.Context, uint64, uint64, string, time.Time) error
}
type MemoryRepository struct {
	mu           sync.Mutex
	next         uint64
	items        map[uint64]*Models.Settlement
	byAssignment map[uint64]bool
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{next: 1, items: map[uint64]*Models.Settlement{}, byAssignment: map[uint64]bool{}}
}
func (r *MemoryRepository) CreateForUser(ctx context.Context, x *Models.Settlement, user uint64) error {
	if user == 0 || x == nil || x.PayerUserID != user || len(x.IdempotencyKey) < 16 || len(x.IdempotencyKey) > 128 {
		return ErrInvalidState
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, existing := range r.items {
		if existing.IdempotencyKey == x.IdempotencyKey {
			if existing.TaskID != x.TaskID || existing.AssignmentID != x.AssignmentID || existing.PayeeUserID != x.PayeeUserID || existing.AmountCents != x.AmountCents || existing.Currency != x.Currency || existing.Method != x.Method {
				return ErrInvalidState
			}
			*x = *existing
			return nil
		}
	}
	if r.byAssignment[x.AssignmentID] {
		return ErrDuplicate
	}
	x.ID = r.next
	r.next++
	x.Status = Models.Pending
	r.items[x.ID] = x
	r.byAssignment[x.AssignmentID] = true
	return nil
}
func (r *MemoryRepository) Create(ctx context.Context, x *Models.Settlement) error {
	if x == nil || x.TaskID == 0 || x.AssignmentID == 0 || x.PayerUserID == 0 || x.PayeeUserID == 0 || x.AmountCents <= 0 || x.PayerUserID == x.PayeeUserID {
		return errors.New("invalid settlement")
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.byAssignment[x.AssignmentID] {
		return ErrDuplicate
	}
	x.ID = r.next
	r.next++
	x.Status = Models.Pending
	r.items[x.ID] = x
	r.byAssignment[x.AssignmentID] = true
	return nil
}
func (r *MemoryRepository) Find(ctx context.Context, id uint64) (*Models.Settlement, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	x, ok := r.items[id]
	if !ok {
		return nil, ErrNotFound
	}
	y := *x
	return &y, nil
}
func (r *MemoryRepository) Claim(ctx context.Context, id, user uint64, at time.Time) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	x, ok := r.items[id]
	if !ok {
		return ErrNotFound
	}
	if x.Status != Models.Pending || x.PayerUserID != user {
		return ErrInvalidState
	}
	x.Status = Models.Claimed
	x.ClaimedBy = &user
	x.UpdatedAt = at
	return nil
}
func (r *MemoryRepository) Confirm(ctx context.Context, id, user uint64, at time.Time) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	x, ok := r.items[id]
	if !ok {
		return ErrNotFound
	}
	if x.Status != Models.Claimed || x.PayeeUserID != user {
		return ErrInvalidState
	}
	x.Status = Models.Confirmed
	x.ConfirmedBy = &user
	x.ConfirmedAt = &at
	x.UpdatedAt = at
	return nil
}
func (r *MemoryRepository) Dispute(ctx context.Context, id, user uint64, at time.Time) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	x, ok := r.items[id]
	if !ok {
		return ErrNotFound
	}
	if user != x.PayerUserID && user != x.PayeeUserID {
		return ErrInvalidState
	}
	if x.Status != Models.Claimed {
		return ErrInvalidState
	}
	x.Status = Models.Disputed
	x.UpdatedAt = at
	return nil
}

func (r *MemoryRepository) ConfirmWithNote(ctx context.Context, id, user uint64, note string, at time.Time) error {
	if strings.TrimSpace(note) == "" || len(note) > 1000 {
		return ErrInvalidState
	}
	if err := r.Confirm(ctx, id, user, at); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if x := r.items[id]; x != nil {
		x.ConfirmationNote = strings.TrimSpace(note)
	}
	return nil
}
func (r *MemoryRepository) DisputeWithReason(ctx context.Context, id, user uint64, reason string, at time.Time) error {
	reason = strings.TrimSpace(reason)
	if len(reason) < 5 || len(reason) > 2000 {
		return ErrInvalidState
	}
	if err := r.Dispute(ctx, id, user, at); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if x := r.items[id]; x != nil {
		x.DisputeReason = reason
	}
	return nil
}
