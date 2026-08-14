package Repositories

import (
	"context"
	"github.com/alumasinde/jijenge/Settlements/Models"
	"testing"
	"time"
)

func TestCashSettlementRequiresPayeeConfirmation(t *testing.T) {
	r := NewMemoryRepository()
	x := &Models.Settlement{TaskID: 1, AssignmentID: 2, PayerUserID: 3, PayeeUserID: 4, Method: Models.Cash, AmountCents: 200000, Currency: "KES", IdempotencyKey: "cash-settlement-test-1234"}
	if e := r.Create(context.Background(), x); e != nil {
		t.Fatal(e)
	}
	if e := r.Confirm(context.Background(), x.ID, 4, time.Now()); e == nil {
		t.Fatal("unclaimed settlement confirmed")
	}
	if e := r.Claim(context.Background(), x.ID, 3, time.Now()); e != nil {
		t.Fatal(e)
	}
	if e := r.Confirm(context.Background(), x.ID, 4, time.Now()); e != nil {
		t.Fatal(e)
	}
}
func TestSettlementDispute(t *testing.T) {
	r := NewMemoryRepository()
	x := &Models.Settlement{TaskID: 1, AssignmentID: 2, PayerUserID: 3, PayeeUserID: 4, Method: Models.Cash, AmountCents: 1, Currency: "KES", IdempotencyKey: "cash-dispute-test-1234"}
	_ = r.Create(context.Background(), x)
	_ = r.Claim(context.Background(), x.ID, 3, time.Now())
	if e := r.Dispute(context.Background(), x.ID, 4, time.Now()); e != nil {
		t.Fatal(e)
	}
}

func TestCashSettlementRequiresEvidenceAndOwnerClaim(t *testing.T) {
	r := NewMemoryRepository()
	x := &Models.Settlement{TaskID: 1, AssignmentID: 2, PayerUserID: 3, PayeeUserID: 4, Method: Models.Cash, AmountCents: 100, Currency: "KES", IdempotencyKey: "cash-evidence-test-1234"}
	if err := r.CreateForUser(context.Background(), x, 4); err == nil {
		t.Fatal("non-payer created settlement")
	}
	if err := r.CreateForUser(context.Background(), x, 3); err != nil {
		t.Fatal(err)
	}
	if err := r.ConfirmWithNote(context.Background(), x.ID, 4, "received", time.Now()); err == nil {
		t.Fatal("unclaimed settlement confirmed")
	}
	if err := r.Claim(context.Background(), x.ID, 3, time.Now()); err != nil {
		t.Fatal(err)
	}
	if err := r.ConfirmWithNote(context.Background(), x.ID, 4, "cash received", time.Now()); err != nil {
		t.Fatal(err)
	}
	got, err := r.Find(context.Background(), x.ID)
	if err != nil {
		t.Fatal(err)
	}
	if got.Status != Models.Confirmed || got.ConfirmationNote != "cash received" {
		t.Fatal("confirmation evidence missing")
	}
}

func TestSettlementIdempotencyReplaysSameRequest(t *testing.T) {
	r := NewMemoryRepository()
	x := &Models.Settlement{TaskID: 1, AssignmentID: 9, PayerUserID: 3, PayeeUserID: 4, Method: Models.Cash, AmountCents: 100, Currency: "KES", IdempotencyKey: "settlement-key-123456"}
	if err := r.CreateForUser(context.Background(), x, 3); err != nil {
		t.Fatal(err)
	}
	first := x.ID
	y := &Models.Settlement{TaskID: 1, AssignmentID: 9, PayerUserID: 3, PayeeUserID: 4, Method: Models.Cash, AmountCents: 100, Currency: "KES", IdempotencyKey: "settlement-key-123456"}
	if err := r.CreateForUser(context.Background(), y, 3); err != nil {
		t.Fatal(err)
	}
	if y.ID != first {
		t.Fatalf("expected replay of %d, got %d", first, y.ID)
	}
}
func TestSettlementIdempotencyRejectsChangedRequest(t *testing.T) {
	r := NewMemoryRepository()
	x := &Models.Settlement{TaskID: 1, AssignmentID: 9, PayerUserID: 3, PayeeUserID: 4, Method: Models.Cash, AmountCents: 100, Currency: "KES", IdempotencyKey: "settlement-key-abcdef"}
	if err := r.CreateForUser(context.Background(), x, 3); err != nil {
		t.Fatal(err)
	}
	y := &Models.Settlement{TaskID: 1, AssignmentID: 9, PayerUserID: 3, PayeeUserID: 4, Method: Models.Cash, AmountCents: 101, Currency: "KES", IdempotencyKey: "settlement-key-abcdef"}
	if err := r.CreateForUser(context.Background(), y, 3); err == nil {
		t.Fatal("changed idempotency request accepted")
	}
}
