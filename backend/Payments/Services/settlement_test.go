package Services

import (
	"context"
	"github.com/alumasinde/jijenge/Financial/Repositories"
	"github.com/alumasinde/jijenge/Payments/Provider"
	paymentrepo "github.com/alumasinde/jijenge/Payments/Repositories"
	"testing"
)

func TestConfiguredSettlementConfirmsPaymentIdempotently(t *testing.T) {
	secret := []byte("01234567890123456789012345678901")
	v, _ := Provider.NewHMACSHA256Verifier("testpsp", secret)
	pr := paymentrepo.NewMemoryRepository()
	s := New(pr, Repositories.NewMemoryRepository(), v)
	s.SetClearingAccountID(99)
	p, err := s.CreatePayment(context.Background(), "testpsp", "provider-2", 1, 2500, "KES")
	if err != nil {
		t.Fatal(err)
	}
	payload := []byte(`{"event_id":"evt-2","payment_ref":"provider-2","status":"success","amount_cents":2500,"currency":"KES"}`)
	processed, err := s.HandleWebhook(context.Background(), payload, sign(secret, payload))
	if err != nil || processed {
		t.Fatalf("first: %v %v", err, processed)
	}
	got, err := pr.GetPaymentByProviderRef(context.Background(), "testpsp", "provider-2")
	if err != nil {
		t.Fatal(err)
	}
	if got.ID != p.ID || got.Status != "confirmed" {
		t.Fatalf("unexpected payment: %+v", got)
	}
	processed, err = s.HandleWebhook(context.Background(), payload, sign(secret, payload))
	if err != nil || !processed {
		t.Fatalf("replay: %v %v", err, processed)
	}
}
