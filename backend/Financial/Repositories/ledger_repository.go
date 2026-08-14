package Repositories

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/alumasinde/jijenge/Financial/Models"
)

var (
	ErrAccountNotFound         = errors.New("account not found")
	ErrAccountFrozen           = errors.New("account is not active")
	ErrCurrencyMismatch        = errors.New("currency mismatch")
	ErrInvalidAmount           = errors.New("invalid amount")
	ErrInsufficientFunds       = errors.New("insufficient funds")
	ErrDuplicateIdempotencyKey = errors.New("idempotency key already used")
	ErrIdempotencyConflict     = errors.New("idempotency key conflicts with request")
	ErrUnbalancedTransaction   = errors.New("unbalanced ledger transaction")
	ErrHoldNotFound            = errors.New("hold not found")
	ErrHoldState               = errors.New("invalid hold state")
	ErrReferenceExists         = errors.New("reference already exists")
)

type LedgerRepository interface {
	CreateAccount(context.Context, *Models.Account) error
	GetAccount(context.Context, uint64) (*Models.Account, error)
	GetBalance(context.Context, uint64) (*Models.Balance, error)
	Transfer(context.Context, string, string, string, uint64, uint64, int64, time.Time) (*Models.Transaction, error)
	CreateHold(context.Context, string, string, uint64, int64, time.Time) (*Models.Hold, error)
	ReleaseHold(context.Context, uint64, time.Time) error
	CaptureHold(context.Context, uint64, uint64, int64, time.Time) error
}

type MemoryRepository struct {
	mu              sync.Mutex
	nextAccount     uint64
	nextTransaction uint64
	nextHold        uint64
	accounts        map[uint64]*Models.Account
	balances        map[uint64]*Models.Balance
	transactions    map[string]*Models.Transaction
	holds           map[uint64]*Models.Hold
	references      map[string]uint64
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{nextAccount: 1, nextTransaction: 1, nextHold: 1,
		accounts: map[uint64]*Models.Account{}, balances: map[uint64]*Models.Balance{},
		transactions: map[string]*Models.Transaction{}, holds: map[uint64]*Models.Hold{},
		references: map[string]uint64{}}
}
func (r *MemoryRepository) CreateAccount(ctx context.Context, a *Models.Account) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if a.Currency == "" {
		return ErrCurrencyMismatch
	}
	a.ID = r.nextAccount
	r.nextAccount++
	r.accounts[a.ID] = cloneAccount(a)
	r.balances[a.ID] = &Models.Balance{AccountID: a.ID, Currency: a.Currency}
	return nil
}
func cloneAccount(a *Models.Account) *Models.Account { x := *a; return &x }
func cloneBalance(b *Models.Balance) *Models.Balance { x := *b; return &x }
func (r *MemoryRepository) GetAccount(ctx context.Context, id uint64) (*Models.Account, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	a, ok := r.accounts[id]
	if !ok {
		return nil, ErrAccountNotFound
	}
	return cloneAccount(a), nil
}
func (r *MemoryRepository) GetBalance(ctx context.Context, id uint64) (*Models.Balance, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	b, ok := r.balances[id]
	if !ok {
		return nil, ErrAccountNotFound
	}
	return cloneBalance(b), nil
}
func (r *MemoryRepository) Transfer(ctx context.Context, key, publicID, desc string, from, to uint64, amount int64, now time.Time) (*Models.Transaction, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if amount <= 0 {
		return nil, ErrInvalidAmount
	}
	if from == to {
		return nil, ErrUnbalancedTransaction
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if old, ok := r.transactions[key]; ok {
		if old.Description != desc || old.Entries[0].AccountID != from || old.Entries[1].AccountID != to || old.Entries[0].DebitCents != amount {
			return nil, ErrIdempotencyConflict
		}
		return cloneTransaction(old), nil
	}
	fa, ok := r.accounts[from]
	if !ok {
		return nil, ErrAccountNotFound
	}
	ta, ok := r.accounts[to]
	if !ok {
		return nil, ErrAccountNotFound
	}
	if fa.Status != Models.AccountActive || ta.Status != Models.AccountActive {
		return nil, ErrAccountFrozen
	}
	if fa.Currency != ta.Currency {
		return nil, ErrCurrencyMismatch
	}
	fb := r.balances[from]
	if fb.AvailableCents < amount {
		return nil, ErrInsufficientFunds
	}
	fb.AvailableCents -= amount
	r.balances[to].AvailableCents += amount
	tx := &Models.Transaction{ID: r.nextTransaction, PublicID: publicID, IdempotencyKey: key, Currency: fa.Currency, Description: desc, CreatedAt: now,
		Entries: []Models.Entry{{AccountID: from, DebitCents: amount}, {AccountID: to, CreditCents: amount}}}
	r.nextTransaction++
	r.transactions[key] = cloneTransaction(tx)
	return tx, nil
}
func cloneTransaction(t *Models.Transaction) *Models.Transaction {
	x := *t
	x.Entries = append([]Models.Entry(nil), t.Entries...)
	return &x
}
func (r *MemoryRepository) CreateHold(ctx context.Context, key, reference string, account uint64, amount int64, now time.Time) (*Models.Hold, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if amount <= 0 {
		return nil, ErrInvalidAmount
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.references[reference]; ok {
		return nil, ErrReferenceExists
	}
	if holdID, ok := r.references[reference]; ok {
		if old, exists := r.holds[holdID]; exists {
			return cloneHold(old), nil
		}
	}
	a, ok := r.accounts[account]
	if !ok {
		return nil, ErrAccountNotFound
	}
	if a.Status != Models.AccountActive {
		return nil, ErrAccountFrozen
	}
	b := r.balances[account]
	if b.AvailableCents < amount {
		return nil, ErrInsufficientFunds
	}
	b.AvailableCents -= amount
	b.HeldCents += amount
	h := &Models.Hold{ID: r.nextHold, PublicID: key, AccountID: account, Reference: reference, AmountCents: amount, Status: Models.HoldActive, CreatedAt: now, UpdatedAt: now}
	r.nextHold++
	r.holds[h.ID] = h
	r.references[reference] = h.ID
	return cloneHold(h), nil
}
func cloneHold(h *Models.Hold) *Models.Hold { x := *h; return &x }
func (r *MemoryRepository) ReleaseHold(ctx context.Context, id uint64, now time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	var h *Models.Hold
	for _, x := range r.holds {
		if x.ID == id {
			h = x
			break
		}
	}
	if h == nil {
		return ErrHoldNotFound
	}
	if h.Status != Models.HoldActive {
		return ErrHoldState
	}
	r.balances[h.AccountID].AvailableCents += h.AmountCents
	r.balances[h.AccountID].HeldCents -= h.AmountCents
	h.Status = Models.HoldReleased
	h.UpdatedAt = now
	return nil
}
func (r *MemoryRepository) CaptureHold(ctx context.Context, id uint64, to uint64, amount int64, now time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if amount <= 0 {
		return ErrInvalidAmount
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	var h *Models.Hold
	for _, x := range r.holds {
		if x.ID == id {
			h = x
			break
		}
	}
	if h == nil {
		return ErrHoldNotFound
	}
	if h.Status != Models.HoldActive {
		return ErrHoldState
	}
	if amount > h.AmountCents {
		return ErrInvalidAmount
	}
	target, ok := r.accounts[to]
	if !ok {
		return ErrAccountNotFound
	}
	source := r.accounts[h.AccountID]
	if target.Currency != source.Currency {
		return ErrCurrencyMismatch
	}
	r.balances[h.AccountID].HeldCents -= amount
	r.balances[to].AvailableCents += amount
	if amount == h.AmountCents {
		h.Status = Models.HoldCaptured
	} else {
		h.AmountCents -= amount
	}
	h.UpdatedAt = now
	return nil
}

// CreditForTest is intentionally not part of LedgerRepository. It exists only
// to make deterministic unit tests able to seed a balance without bypassing
// production ledger APIs.
func (r *MemoryRepository) CreditForTest(account uint64, amount int64) error {
	if amount <= 0 {
		return ErrInvalidAmount
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.accounts[account]; !ok {
		return ErrAccountNotFound
	}
	r.balances[account].AvailableCents += amount
	return nil
}
