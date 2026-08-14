package Repositories

import (
	"context"
	"github.com/alumasinde/jijenge/Escrow/Models"
	"testing"
	"time"
)

func TestMemoryEscrowLifecycle(t *testing.T) {
	r := NewMemoryRepository()
	now := time.Now()
	e := &Models.Escrow{TaskID: 1, AssignmentID: 2, PayerAccountID: 3, WorkerAccountID: 4, AmountCents: 1000, Currency: "KES", CreatedAt: now, UpdatedAt: now}
	if err := r.CreateAndFund(context.Background(), e); err != nil {
		t.Fatal(err)
	}
	if err := r.MarkSubmitted(context.Background(), e.ID, now); err != nil {
		t.Fatal(err)
	}
	d, err := r.OpenDispute(context.Background(), e.ID, 9, "quality issue", now)
	if err != nil {
		t.Fatal(err)
	}
	if err := r.ResolveDispute(context.Background(), d.ID, SplitSettlement, 700, 8, now); err != nil {
		t.Fatal(err)
	}
	x, _ := r.Get(context.Background(), e.ID)
	if x.Status != Models.Released || x.PlatformFeeCents != 300 {
		t.Fatalf("unexpected %+v", x)
	}
	if err := r.ResolveDispute(context.Background(), d.ID, PayWorker, 1000, 0, now); err != ErrResolutionExists {
		t.Fatalf("got %v", err)
	}
}

func TestRefund(t *testing.T) {
	r := NewMemoryRepository()
	now := time.Now()
	e := &Models.Escrow{TaskID: 1, AssignmentID: 2, PayerAccountID: 3, WorkerAccountID: 4, AmountCents: 1000, Currency: "KES", CreatedAt: now, UpdatedAt: now}
	if err := r.CreateAndFund(context.Background(), e); err != nil {
		t.Fatal(err)
	}
	if err := r.MarkSubmitted(context.Background(), e.ID, now); err != nil {
		t.Fatal(err)
	}
	d, _ := r.OpenDispute(context.Background(), e.ID, 9, "not completed", now)
	if err := r.ResolveDispute(context.Background(), d.ID, RefundPayer, 0, 0, now); err != nil {
		t.Fatal(err)
	}
	x, _ := r.Get(context.Background(), e.ID)
	if x.Status != Models.Refunded {
		t.Fatalf("unexpected %s", x.Status)
	}
}

func TestEscrowIdempotencyReplaysSameRequest(t *testing.T) {
	r := NewMemoryRepository()
	x := &Models.Escrow{TaskID: 1, AssignmentID: 8, PayerAccountID: 11, WorkerAccountID: 12, PayerUserID: 3, AmountCents: 100, Currency: "KES", IdempotencyKey: "escrow-key-123456"}
	if err := r.CreateAndFundForUser(context.Background(), x, 3); err != nil {
		t.Fatal(err)
	}
	first := x.ID
	y := &Models.Escrow{TaskID: 1, AssignmentID: 8, PayerAccountID: 11, WorkerAccountID: 12, PayerUserID: 3, AmountCents: 100, Currency: "KES", IdempotencyKey: "escrow-key-123456"}
	if err := r.CreateAndFundForUser(context.Background(), y, 3); err != nil {
		t.Fatal(err)
	}
	if y.ID != first {
		t.Fatalf("expected replay of %d, got %d", first, y.ID)
	}
}
func TestEscrowIdempotencyRejectsChangedRequest(t *testing.T) {
	r := NewMemoryRepository()
	x := &Models.Escrow{TaskID: 1, AssignmentID: 8, PayerAccountID: 11, WorkerAccountID: 12, PayerUserID: 3, AmountCents: 100, Currency: "KES", IdempotencyKey: "escrow-key-abcdef"}
	if err := r.CreateAndFundForUser(context.Background(), x, 3); err != nil {
		t.Fatal(err)
	}
	y := &Models.Escrow{TaskID: 1, AssignmentID: 8, PayerAccountID: 11, WorkerAccountID: 12, PayerUserID: 3, AmountCents: 101, Currency: "KES", IdempotencyKey: "escrow-key-abcdef"}
	if err := r.CreateAndFundForUser(context.Background(), y, 3); err == nil {
		t.Fatal("changed idempotency request accepted")
	}
}
