package Middleware

import (
	"net/http"
	"sync"
	"time"

	"github.com/alumasinde/jijenge/Core/HTTP"
)

type RateLimiter struct {
	mu      sync.Mutex
	entries map[string]*rateEntry
	limit   int
	window  time.Duration
	maxKeys int
}

type rateEntry struct {
	count       int
	windowStart time.Time
}

func NewRateLimiter(limit int, window time.Duration, maxKeys int) *RateLimiter {
	if limit < 1 {
		limit = 1
	}
	if window <= 0 {
		window = time.Minute
	}
	if maxKeys < 100 {
		maxKeys = 10_000
	}
	return &RateLimiter{
		entries: make(map[string]*rateEntry),
		limit:   limit,
		window:  window,
		maxKeys: maxKeys,
	}
}

func (l *RateLimiter) Allow(key string, now time.Time) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	if len(l.entries) >= l.maxKeys {
		l.evictExpired(now)
		if len(l.entries) >= l.maxKeys {
			return false
		}
	}

	entry, ok := l.entries[key]
	if !ok || now.Sub(entry.windowStart) >= l.window {
		l.entries[key] = &rateEntry{count: 1, windowStart: now}
		return true
	}

	if entry.count >= l.limit {
		return false
	}

	entry.count++
	return true
}

func (l *RateLimiter) evictExpired(now time.Time) {
	for key, entry := range l.entries {
		if now.Sub(entry.windowStart) >= l.window {
			delete(l.entries, key)
		}
	}
}

func RateLimit(limiter *RateLimiter, keyFunc func(*http.Request) string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			key := keyFunc(r)
			if key == "" {
				key = "anonymous"
			}
			if !limiter.Allow(key, time.Now()) {
				w.Header().Set("Retry-After", "60")
				HTTP.ErrorResponse(w, http.StatusTooManyRequests,
					"RATE_LIMITED", "Too many requests")
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

// ConditionalRateLimit applies the limiter only when keyFunc returns a non-empty
// key. It is useful for protecting a small set of sensitive routes without
// imposing their stricter limit on the rest of the API.
func ConditionalRateLimit(limiter *RateLimiter, keyFunc func(*http.Request) string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			key := keyFunc(r)
			if key == "" {
				next.ServeHTTP(w, r)
				return
			}
			if !limiter.Allow(key, time.Now()) {
				w.Header().Set("Retry-After", "60")
				HTTP.ErrorResponse(w, http.StatusTooManyRequests, "RATE_LIMITED", "Too many requests")
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
