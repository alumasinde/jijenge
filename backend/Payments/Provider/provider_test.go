package Provider

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"testing"
)

func TestHMACSHA256Verifier(t *testing.T) {
	v, err := NewHMACSHA256Verifier("test", []byte("01234567890123456789012345678901"))
	if err != nil {
		t.Fatal(err)
	}
	payload := []byte(`{"event_id":"evt-1","payment_ref":"pay-1"}`)
	m := hmac.New(sha256.New, v.Secret)
	m.Write(payload)
	sig := hex.EncodeToString(m.Sum(nil))
	if !v.Verify(payload, sig) {
		t.Fatal("valid signature rejected")
	}
	if v.Verify(payload, sig[:len(sig)-2]+"00") {
		t.Fatal("invalid signature accepted")
	}
	if v.Verify(payload, "not-hex") {
		t.Fatal("malformed signature accepted")
	}
}

func TestHMACVerifierRequiresStrongSecret(t *testing.T) {
	if _, err := NewHMACSHA256Verifier("test", []byte("short")); err == nil {
		t.Fatal("expected weak secret to be rejected")
	}
}
