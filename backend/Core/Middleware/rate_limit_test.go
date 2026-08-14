package Middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestRateLimiter(t *testing.T) {
	l := NewRateLimiter(2, time.Minute, 100)
	now := time.Now()

	if !l.Allow("a", now) || !l.Allow("a", now) {
		t.Fatal("first two requests should be allowed")
	}
	if l.Allow("a", now) {
		t.Fatal("third request should be rejected")
	}
	if !l.Allow("b", now) {
		t.Fatal("different key should be allowed")
	}
}

func TestRateLimitMiddleware(t *testing.T) {
	l := NewRateLimiter(1, time.Minute, 100)
	handler := RateLimit(l, func(r *http.Request) string { return r.RemoteAddr })(
		http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNoContent)
		}),
	)

	req1 := httptest.NewRequest(http.MethodGet, "/", nil)
	rec1 := httptest.NewRecorder()
	handler.ServeHTTP(rec1, req1)
	if rec1.Code != http.StatusNoContent {
		t.Fatalf("expected first request 204, got %d", rec1.Code)
	}

	req2 := httptest.NewRequest(http.MethodGet, "/", nil)
	rec2 := httptest.NewRecorder()
	handler.ServeHTTP(rec2, req2)
	if rec2.Code != http.StatusTooManyRequests {
		t.Fatalf("expected second request 429, got %d", rec2.Code)
	}
}
