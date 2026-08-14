package Repositories

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Audit/Models"
	"sync"
	"time"
)

type Repository interface {
	Record(context.Context, *Models.AuditEvent) error
	VerifyChain(context.Context) error
	StartRun(context.Context, *Models.ReconciliationRun) error
	AddIssue(context.Context, *Models.ReconciliationIssue) error
	FinishRun(context.Context, uint64, string, int64, int64, int64, time.Time) error
}

type MemoryRepository struct {
	mu                       sync.Mutex
	next, runNext, issueNext uint64
	Events                   []Models.AuditEvent
	Runs                     map[uint64]Models.ReconciliationRun
	Issues                   []Models.ReconciliationIssue
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{next: 1, runNext: 1, issueNext: 1, Runs: map[uint64]Models.ReconciliationRun{}}
}
func (r *MemoryRepository) Record(ctx context.Context, e *Models.AuditEvent) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if e == nil {
		return errors.New("nil audit event")
	}
	e.ID = r.next
	r.next++
	if len(r.Events) > 0 {
		e.PreviousHash = r.Events[len(r.Events)-1].EventHash
	}
	e.EventHash = Models.EventHash(e, e.PreviousHash)
	r.Events = append(r.Events, *e)
	return nil
}

func (r *MemoryRepository) VerifyChain(ctx context.Context) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	var previous string
	for i := range r.Events {
		e := &r.Events[i]
		if e.EventHash == "" {
			previous = ""
			continue
		}
		if e.PreviousHash != previous || e.EventHash != Models.EventHash(e, e.PreviousHash) {
			return errors.New("audit chain integrity failure")
		}
		previous = e.EventHash
	}
	return nil
}
func (r *MemoryRepository) StartRun(ctx context.Context, x *Models.ReconciliationRun) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	x.ID = r.runNext
	r.runNext++
	r.Runs[x.ID] = *x
	return nil
}
func (r *MemoryRepository) AddIssue(ctx context.Context, x *Models.ReconciliationIssue) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	x.ID = r.issueNext
	r.issueNext++
	r.Issues = append(r.Issues, *x)
	return nil
}
func (r *MemoryRepository) FinishRun(ctx context.Context, id uint64, status string, a, t, d int64, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	x, ok := r.Runs[id]
	if !ok {
		return context.Canceled
	}
	x.Status = status
	x.AccountsChecked = a
	x.TransactionsChecked = t
	x.Discrepancies = d
	x.FinishedAt = &at
	r.Runs[id] = x
	return nil
}
