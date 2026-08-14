package Repositories

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/alumasinde/jijenge/Escrow/Models"
)

var (
	ErrEscrowNotFound    = errors.New("escrow not found")
	ErrEscrowExists      = errors.New("escrow already exists")
	ErrEscrowState       = errors.New("invalid escrow state")
	ErrInvalidResolution = errors.New("invalid dispute resolution")
	ErrDisputeNotFound   = errors.New("dispute not found")
	ErrDisputeExists     = errors.New("dispute already exists")
	ErrResolutionExists  = errors.New("dispute already resolved")
)

type DisputeResolution string

const (
	PayWorker       DisputeResolution = "pay_worker"
	RefundPayer     DisputeResolution = "refund_payer"
	SplitSettlement DisputeResolution = "split_settlement"
)

type Dispute struct {
	ID             uint64
	PublicID       string
	EscrowID       uint64
	OpenedByUserID uint64
	Reason         string
	Status         string
	CreatedAt      time.Time
	ResolvedAt     *time.Time
	Resolution     *DisputeResolution
}

type Repository interface {
	CreateAndFund(context.Context, *Models.Escrow) error
	CreateAndFundForUser(context.Context, *Models.Escrow, uint64) error
	Get(context.Context, uint64) (*Models.Escrow, error)
	GetByAssignment(context.Context, uint64) (*Models.Escrow, error)
	MarkSubmitted(context.Context, uint64, time.Time) error
	SubmitAssignment(context.Context, uint64, time.Time) error
	ReleaseVerifiedAssignment(context.Context, uint64, time.Time) error
	ReleaseVerifiedAssignmentForUser(context.Context, uint64, uint64, time.Time) error
	Release(context.Context, uint64, time.Time) error
	ReleaseWithFee(context.Context, uint64, int64, uint64, time.Time) error
	Refund(context.Context, uint64, time.Time) error
	OpenDispute(context.Context, uint64, uint64, string, time.Time) (*Dispute, error)
	ResolveDispute(context.Context, uint64, DisputeResolution, int64, uint64, time.Time) error
}

type MemoryRepository struct {
	mu                sync.Mutex
	next, nextDispute uint64
	items             map[uint64]*Models.Escrow
	disputes          map[uint64]*Dispute
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{next: 1, nextDispute: 1, items: map[uint64]*Models.Escrow{}, disputes: map[uint64]*Dispute{}}
}
func clone(e *Models.Escrow) *Models.Escrow { x := *e; return &x }
func cloneDispute(d *Dispute) *Dispute      { x := *d; return &x }
func (r *MemoryRepository) CreateAndFundForUser(ctx context.Context, e *Models.Escrow, userID uint64) error {
	if e == nil || userID == 0 || e.PayerUserID != 0 && e.PayerUserID != userID || len(e.IdempotencyKey) < 16 || len(e.IdempotencyKey) > 128 {
		return ErrInvalidResolution
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, x := range r.items {
		if x.IdempotencyKey == e.IdempotencyKey {
			if x.TaskID != e.TaskID || x.AssignmentID != e.AssignmentID || x.AmountCents != e.AmountCents || x.Currency != e.Currency || x.PayerAccountID != e.PayerAccountID || x.WorkerAccountID != e.WorkerAccountID || x.PayerUserID != userID {
				return ErrInvalidResolution
			}
			*e = *clone(x)
			return nil
		}
		if x.AssignmentID == e.AssignmentID {
			return ErrEscrowExists
		}
	}
	e.ID = r.next
	r.next++
	e.PayerUserID = userID
	e.Status = Models.Funded
	r.items[e.ID] = clone(e)
	return nil
}
func (r *MemoryRepository) CreateAndFund(ctx context.Context, e *Models.Escrow) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, x := range r.items {
		if x.AssignmentID == e.AssignmentID {
			return ErrEscrowExists
		}
	}
	e.ID = r.next
	r.next++
	e.Status = Models.Funded
	r.items[e.ID] = clone(e)
	return nil
}
func (r *MemoryRepository) Get(ctx context.Context, id uint64) (*Models.Escrow, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	e, ok := r.items[id]
	if !ok {
		return nil, ErrEscrowNotFound
	}
	return clone(e), nil
}
func (r *MemoryRepository) GetByAssignment(ctx context.Context, assignmentID uint64) (*Models.Escrow, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, e := range r.items {
		if e.AssignmentID == assignmentID {
			return clone(e), nil
		}
	}
	return nil, ErrEscrowNotFound
}
func (r *MemoryRepository) SubmitAssignment(ctx context.Context, assignmentID uint64, at time.Time) error {
	e, err := r.GetByAssignment(ctx, assignmentID)
	if err != nil {
		return err
	}
	return r.MarkSubmitted(ctx, e.ID, at)
}
func (r *MemoryRepository) ReleaseVerifiedAssignmentForUser(ctx context.Context, assignmentID, userID uint64, at time.Time) error {
	if userID == 0 {
		return ErrInvalidResolution
	}
	e, err := r.GetByAssignment(ctx, assignmentID)
	if err != nil {
		return err
	}
	if e.PayerUserID != 0 && e.PayerUserID != userID {
		return ErrInvalidResolution
	}
	return r.Release(ctx, e.ID, at)
}

func (r *MemoryRepository) ReleaseVerifiedAssignment(ctx context.Context, assignmentID uint64, at time.Time) error {
	e, err := r.GetByAssignment(ctx, assignmentID)
	if err != nil {
		return err
	}
	return r.Release(ctx, e.ID, at)
}

func (r *MemoryRepository) MarkSubmitted(ctx context.Context, id uint64, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	e, ok := r.items[id]
	if !ok {
		return ErrEscrowNotFound
	}
	if e.Status != Models.Funded {
		return ErrEscrowState
	}
	e.Status = Models.Submitted
	e.UpdatedAt = at
	return nil
}
func (r *MemoryRepository) Release(ctx context.Context, id uint64, at time.Time) error {
	return r.ReleaseWithFee(ctx, id, 0, 0, at)
}
func (r *MemoryRepository) ReleaseWithFee(ctx context.Context, id uint64, fee int64, feeAccount uint64, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	e, ok := r.items[id]
	if !ok {
		return ErrEscrowNotFound
	}
	if e.Status == Models.Released {
		return nil
	}
	if e.Status != Models.Submitted && e.Status != Models.VerificationPending {
		return ErrEscrowState
	}
	if fee > e.AmountCents {
		return ErrInvalidResolution
	}
	if fee > 0 && feeAccount == 0 {
		return ErrInvalidResolution
	}
	e.PlatformFeeCents = fee
	e.Status = Models.Released
	e.ReleasedAt = &at
	e.UpdatedAt = at
	return nil
}
func (r *MemoryRepository) Refund(ctx context.Context, id uint64, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	e, ok := r.items[id]
	if !ok {
		return ErrEscrowNotFound
	}
	if e.Status == Models.Refunded {
		return nil
	}
	if e.Status == Models.Released || e.Status == Models.Cancelled {
		return ErrEscrowState
	}
	if e.Status != Models.Funded && e.Status != Models.Submitted && e.Status != Models.VerificationPending && e.Status != Models.Disputed {
		return ErrEscrowState
	}
	e.Status = Models.Refunded
	e.UpdatedAt = at
	return nil
}
func (r *MemoryRepository) OpenDispute(ctx context.Context, id, user uint64, reason string, at time.Time) (*Dispute, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if user == 0 || reason == "" {
		return nil, ErrInvalidResolution
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	e, ok := r.items[id]
	if !ok {
		return nil, ErrEscrowNotFound
	}
	if e.Status != Models.Submitted && e.Status != Models.VerificationPending {
		return nil, ErrEscrowState
	}
	for _, d := range r.disputes {
		if d.EscrowID == id && d.Status == "open" {
			return nil, ErrDisputeExists
		}
	}
	d := &Dispute{ID: r.nextDispute, EscrowID: id, OpenedByUserID: user, Reason: reason, Status: "open", CreatedAt: at}
	r.nextDispute++
	e.Status = Models.Disputed
	e.DisputeID = &d.ID
	e.UpdatedAt = at
	r.disputes[d.ID] = d
	return cloneDispute(d), nil
}
func (r *MemoryRepository) ResolveDispute(ctx context.Context, id uint64, res DisputeResolution, workerCents int64, feeAccount uint64, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	d, ok := r.disputes[id]
	if !ok {
		return ErrDisputeNotFound
	}
	if d.Status != "open" {
		return ErrResolutionExists
	}
	e, ok := r.items[d.EscrowID]
	if !ok {
		return ErrEscrowNotFound
	}
	if res != PayWorker && res != RefundPayer && res != SplitSettlement {
		return ErrInvalidResolution
	}
	if workerCents < 0 || workerCents > e.AmountCents {
		return ErrInvalidResolution
	}
	if res == PayWorker && workerCents != e.AmountCents {
		return ErrInvalidResolution
	}
	if res == RefundPayer && workerCents != 0 {
		return ErrInvalidResolution
	}
	if res == SplitSettlement && workerCents <= 0 || res == SplitSettlement && workerCents >= e.AmountCents {
		return ErrInvalidResolution
	}
	if res == SplitSettlement && feeAccount == 0 {
		return ErrInvalidResolution
	}
	d.Status = "resolved"
	d.ResolvedAt = &at
	d.Resolution = &res
	if res == RefundPayer {
		e.Status = Models.Refunded
	} else {
		e.Status = Models.Released
		e.PlatformFeeCents = e.AmountCents - workerCents
	}
	e.ReleasedAt = &at
	e.UpdatedAt = at
	return nil
}
