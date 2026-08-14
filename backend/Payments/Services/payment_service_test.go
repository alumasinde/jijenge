package Services

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"testing"

	financialrepo "github.com/alumasinde/jijenge/Financial/Repositories"
	"github.com/alumasinde/jijenge/Payments/Provider"
	paymentrepo "github.com/alumasinde/jijenge/Payments/Repositories"
)

func sign(secret, payload []byte) string {
	m := hmac.New(sha256.New, secret)
	_, _ = m.Write(payload)
	return hex.EncodeToString(m.Sum(nil))
}

func TestWebhookVerificationAndReplay(t *testing.T) {
	secret := []byte("01234567890123456789012345678901")
	v, _ := Provider.NewHMACSHA256Verifier("testpsp", secret)
	pr := paymentrepo.NewMemoryRepository()
	pay := New(pr, financialrepo.NewMemoryRepository(), v)
	if _, err := pay.CreatePayment(context.Background(), "testpsp", "provider-1", 1, 5000, "KES"); err != nil {
		t.Fatal(err)
	}
	payload := []byte(`{"event_id":"evt-1","payment_ref":"provider-1","status":"success","amount_cents":5000,"currency":"KES"}`)
	processed, err := pay.HandleWebhook(context.Background(), payload, sign(secret, payload))
	if err != nil || processed {
		t.Fatalf("first webhook: %v %v", err, processed)
	}
	processed, err = pay.HandleWebhook(context.Background(), payload, sign(secret, payload))
	if err != nil || !processed {
		t.Fatalf("replay: %v %v", err, processed)
	}
}

func TestInvalidSignatureRejected(t *testing.T) {
	secret := []byte("01234567890123456789012345678901")
	v, _ := Provider.NewHMACSHA256Verifier("testpsp", secret)
	pay := New(paymentrepo.NewMemoryRepository(), financialrepo.NewMemoryRepository(), v)
	_, err := pay.HandleWebhook(context.Background(), []byte(`{"event_id":"e","payment_ref":"p","status":"success","amount_cents":1,"currency":"KES"}`), "bad")
	if err != Provider.ErrInvalidSignature {
		t.Fatalf("got %v", err)
	}
}
