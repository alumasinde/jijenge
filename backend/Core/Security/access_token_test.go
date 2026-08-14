package Security

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestBearerToken(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer abc123")
	got, err := BearerToken(req)
	if err != nil || got != "abc123" {
		t.Fatalf("unexpected token result: %q %v", got, err)
	}
}

func TestBearerTokenRejectsMalformed(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Basic abc")
	if _, err := BearerToken(req); err == nil {
		t.Fatal("expected malformed auth header to fail")
	}
}
