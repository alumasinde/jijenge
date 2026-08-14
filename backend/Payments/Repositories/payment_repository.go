package Repositories

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/alumasinde/jijenge/Payments/Models"
)

var (
	ErrPaymentNotFound         = errors.New("payment not found")
	ErrWebhookAlreadyProcessed = errors.New("webhook already processed")
	ErrWebhookConflict         = errors.New("webhook conflicts with stored event")
	ErrProviderEventConflict   = errors.New("provider event conflicts with confirmed payment")
	ErrPaymentState            = errors.New("invalid payment state")
	ErrProviderRefExists       = errors.New("provider reference already exists")
)

type Repository interface {
	CreatePayment(context.Context, *Models.Payment) error
	GetPaymentByProviderRef(context.Context, string, string) (*Models.Payment, error)
	RecordWebhook(context.Context, *Models.WebhookEvent) (bool, error)
	MarkWebhookProcessed(context.Context, uint64, time.Time) error
	ConfirmPayment(context.Context, uint64, string, string, time.Time) error
	FailPayment(context.Context, uint64, string, time.Time) error
	SettleConfirmedPayment(context.Context, uint64, uint64, string, time.Time) error
	ConfirmAndSettlePayment(context.Context, uint64, string, string, uint64, string, time.Time) error
}

type MemoryRepository struct {
	mu                     sync.Mutex
	nextPayment, nextEvent uint64
	payments               map[uint64]*Models.Payment
	byProviderRef          map[string]uint64
	events                 map[string]*Models.WebhookEvent
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{nextPayment: 1, nextEvent: 1, payments: map[uint64]*Models.Payment{}, byProviderRef: map[string]uint64{}, events: map[string]*Models.WebhookEvent{}}
}
func (r *MemoryRepository) CreatePayment(ctx context.Context, p *Models.Payment) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	k := p.Provider + ":" + p.ProviderRef
	if _, ok := r.byProviderRef[k]; ok {
		return ErrProviderRefExists
	}
	p.ID = r.nextPayment
	r.nextPayment++
	r.payments[p.ID] = clonePayment(p)
	r.byProviderRef[k] = p.ID
	return nil
}
func clonePayment(p *Models.Payment) *Models.Payment         { x := *p; return &x }
func cloneEvent(e *Models.WebhookEvent) *Models.WebhookEvent { x := *e; return &x }
func (r *MemoryRepository) GetPaymentByProviderRef(ctx context.Context, provider, ref string) (*Models.Payment, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	id, ok := r.byProviderRef[provider+":"+ref]
	if !ok {
		return nil, ErrPaymentNotFound
	}
	return clonePayment(r.payments[id]), nil
}
func (r *MemoryRepository) RecordWebhook(ctx context.Context, e *Models.WebhookEvent) (bool, error) {
	if err := ctx.Err(); err != nil {
		return false, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if old, ok := r.events[e.Provider+":"+e.EventID]; ok {
		if old.PayloadHash != e.PayloadHash {
			return false, ErrWebhookConflict
		}
		return old.Processed, nil
	}
	e.ID = r.nextEvent
	r.nextEvent++
	r.events[e.Provider+":"+e.EventID] = cloneEvent(e)
	return false, nil
}
func (r *MemoryRepository) MarkWebhookProcessed(ctx context.Context, id uint64, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, e := range r.events {
		if e.ID == id {
			e.Processed = true
			e.ProcessedAt = &at
			return nil
		}
	}
	return ErrPaymentNotFound
}
func (r *MemoryRepository) ConfirmPayment(ctx context.Context, id uint64, providerRef, eventID string, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.payments[id]
	if !ok {
		return ErrPaymentNotFound
	}
	if p.Status == Models.StatusConfirmed {
		return nil
	}
	if p.Status != Models.StatusPending {
		return ErrPaymentState
	}
	p.Status = Models.StatusConfirmed
	p.ProviderRef = providerRef
	p.ProviderEventID = eventID
	p.UpdatedAt = at
	return nil
}
func (r *MemoryRepository) FailPayment(ctx context.Context, id uint64, reason string, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.payments[id]
	if !ok {
		return ErrPaymentNotFound
	}
	if p.Status == Models.StatusConfirmed {
		return ErrPaymentState
	}
	if p.Status == Models.StatusFailed {
		return nil
	}
	p.Status = Models.StatusFailed
	p.UpdatedAt = at
	return nil
}

func (r *MemoryRepository) SettleConfirmedPayment(ctx context.Context, paymentID, clearingAccountID uint64, idem string, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.payments[paymentID]
	if !ok {
		return ErrPaymentNotFound
	}
	if p.Status != Models.StatusConfirmed {
		return ErrPaymentState
	}
	// The memory payment repository deliberately does not mutate the financial
	// ledger. Atomic settlement is implemented by the MySQL repository where
	// payments and ledger rows share one InnoDB transaction.
	return nil
}

func (r *MemoryRepository) ConfirmAndSettlePayment(ctx context.Context, paymentID uint64, providerRef, eventID string, clearingAccountID uint64, idem string, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.payments[paymentID]
	if !ok {
		return ErrPaymentNotFound
	}
	if p.Status == Models.StatusConfirmed {
		return nil
	}
	if p.Status != Models.StatusPending {
		return ErrPaymentState
	}
	p.Status = Models.StatusConfirmed
	p.ProviderRef = providerRef
	p.ProviderEventID = eventID
	p.UpdatedAt = at
	return nil
}
