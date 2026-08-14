package Services

import (
	"context"
	"github.com/alumasinde/jijenge/Financial/Repositories"
	"testing"
)

func TestTransferIsIdempotent(t *testing.T) {
	r := Repositories.NewMemoryRepository()
	s := New(r)
	ctx := context.Background()
	a, _ := s.CreateAccount(ctx, nil, "KES")
	b, _ := s.CreateAccount(ctx, nil, "KES")
	if err := r.CreditForTest(a.ID, 1000); err != nil {
		t.Fatal(err)
	}
	first, err := s.Transfer(ctx, "k1", "payment", a.ID, b.ID, 100)
	if err != nil {
		t.Fatal(err)
	}
	second, err := s.Transfer(ctx, "k1", "payment", a.ID, b.ID, 100)
	if err != nil {
		t.Fatal(err)
	}
	if first.PublicID != second.PublicID {
		t.Fatal("idempotent retry returned a different transaction")
	}
	ba, _ := r.GetBalance(ctx, a.ID)
	bb, _ := r.GetBalance(ctx, b.ID)
	if ba.AvailableCents != 900 || bb.AvailableCents != 100 {
		t.Fatalf("bad balances: %+v %+v", ba, bb)
	}
	if _, err := s.Transfer(ctx, "k1", "different", a.ID, b.ID, 100); err != Repositories.ErrIdempotencyConflict {
		t.Fatalf("got %v", err)
	}
}
func TestTransferRejectsCurrencyMismatch(t *testing.T) {
	r := Repositories.NewMemoryRepository()
	s := New(r)
	a, _ := s.CreateAccount(context.Background(), nil, "KES")
	b, _ := s.CreateAccount(context.Background(), nil, "USD")
	if _, err := s.Transfer(context.Background(), "k", "x", a.ID, b.ID, 1); err != Repositories.ErrCurrencyMismatch {
		t.Fatalf("got %v", err)
	}
}
func TestHoldLifecycle(t *testing.T) {
	r := Repositories.NewMemoryRepository()
	s := New(r)
	ctx := context.Background()
	a, _ := s.CreateAccount(ctx, nil, "KES")
	b, _ := s.CreateAccount(ctx, nil, "KES")
	_ = r.CreditForTest(a.ID, 1000)
	h, err := s.PlaceHold(ctx, "hk", "order-1", a.ID, 600)
	if err != nil {
		t.Fatal(err)
	}
	bal, _ := r.GetBalance(ctx, a.ID)
	if bal.AvailableCents != 400 || bal.HeldCents != 600 {
		t.Fatal(bal)
	}
	if err := s.CaptureHold(ctx, h.ID, b.ID, 600); err != nil {
		t.Fatal(err)
	}
	bal, _ = r.GetBalance(ctx, a.ID)
	bb, _ := r.GetBalance(ctx, b.ID)
	if bal.HeldCents != 0 || bb.AvailableCents != 600 {
		t.Fatalf("bad capture: %+v %+v", bal, bb)
	}
}
