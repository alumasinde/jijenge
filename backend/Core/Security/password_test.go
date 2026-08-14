package Security

import (
	"testing"
)

func TestPasswordHashAndVerify(t *testing.T) {
	hash, err := HashPassword("correct horse battery staple")
	if err != nil {
		t.Fatal(err)
	}

	if hash == "correct horse battery staple" {
		t.Fatal("password was returned in plaintext")
	}

	ok, err := VerifyPassword("correct horse battery staple", hash)
	if err != nil {
		t.Fatal(err)
	}
	if !ok {
		t.Fatal("expected password verification to succeed")
	}

	ok, err = VerifyPassword("wrong password", hash)
	if err != nil {
		t.Fatal(err)
	}
	if ok {
		t.Fatal("expected wrong password to fail")
	}

	hash2, err := HashPassword("correct horse battery staple")
	if err != nil {
		t.Fatal(err)
	}
	if hash == hash2 {
		t.Fatal("expected unique salts to produce different hashes")
	}
}

func TestPasswordRejectsMalformedHash(t *testing.T) {
	if _, err := VerifyPassword("password", "not-a-valid-hash"); err == nil {
		t.Fatal("expected malformed hash to fail")
	}
}

func TestPasswordNeedsRehash(t *testing.T) {
	hash, err := HashPassword("correct horse battery staple")
	if err != nil {
		t.Fatal(err)
	}
	if PasswordNeedsRehash(hash) {
		t.Fatal("fresh hash should not need rehash")
	}
}

func TestToken(t *testing.T) {
	token, err := GenerateToken(32)
	if err != nil {
		t.Fatal(err)
	}
	if len(token) < 40 {
		t.Fatalf("token unexpectedly short: %d", len(token))
	}

	h1 := HashToken(token)
	h2 := HashToken(token)
	if !ConstantTimeEqual(h1[:], h2[:]) {
		t.Fatal("same token should produce same hash")
	}
}
