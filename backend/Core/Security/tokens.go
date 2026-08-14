package Security

import (
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"errors"
)

var ErrRandomGeneration = errors.New("secure random generation failed")

// GenerateToken returns a URL-safe, high-entropy opaque token.
// Store only its hash when the token needs to be persisted.
func GenerateToken(bytes int) (string, error) {
	if bytes < 32 || bytes > 256 {
		return "", errors.New("token size must be between 32 and 256 bytes")
	}
	raw := make([]byte, bytes)
	if _, err := rand.Read(raw); err != nil {
		return "", ErrRandomGeneration
	}
	return base64.RawURLEncoding.EncodeToString(raw), nil
}

func HashToken(token string) [32]byte {
	return sha256.Sum256([]byte(token))
}

func ConstantTimeEqual(a, b []byte) bool {
	if len(a) != len(b) {
		return false
	}
	return subtle.ConstantTimeCompare(a, b) == 1
}
