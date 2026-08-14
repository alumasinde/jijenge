package Provider

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"errors"
)

var ErrInvalidSignature = errors.New("invalid provider signature")

// Verifier abstracts a PSP's webhook authentication mechanism.
// The provider adapter is responsible for normalizing the raw request into
// a canonical byte sequence before calling Verify.
type Verifier interface {
	Name() string
	Verify(payload []byte, signature string) bool
}

type HMACSHA256Verifier struct {
	ProviderName string
	Secret       []byte
}

func NewHMACSHA256Verifier(name string, secret []byte) (*HMACSHA256Verifier, error) {
	if name == "" || len(secret) < 32 {
		return nil, errors.New("provider name and 32+ byte secret are required")
	}
	cp := append([]byte(nil), secret...)
	return &HMACSHA256Verifier{ProviderName: name, Secret: cp}, nil
}
func (v *HMACSHA256Verifier) Name() string { return v.ProviderName }
func (v *HMACSHA256Verifier) Verify(payload []byte, signature string) bool {
	raw, err := hex.DecodeString(signature)
	if err != nil {
		return false
	}
	mac := hmac.New(sha256.New, v.Secret)
	_, _ = mac.Write(payload)
	return hmac.Equal(mac.Sum(nil), raw)
}
