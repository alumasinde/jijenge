package Config

import (
	"testing"
	"time"
)

func TestLoadDefaults(t *testing.T) {
	t.Setenv("APP_PORT", "")
	t.Setenv("APP_MAX_BODY_BYTES", "")
	t.Setenv("APP_RATE_LIMIT_REQUESTS", "")
	t.Setenv("APP_RATE_LIMIT_WINDOW", "")
	cfg := Load()

	if cfg.Port != "8080" {
		t.Fatalf("expected default port 8080, got %q", cfg.Port)
	}
	if cfg.MaxBodyBytes != 1<<20 {
		t.Fatalf("expected 1 MiB body limit, got %d", cfg.MaxBodyBytes)
	}
	if cfg.ReadTimeout != 10*time.Second {
		t.Fatalf("expected 10s read timeout, got %s", cfg.ReadTimeout)
	}
	if cfg.RateLimitRequests != 120 {
		t.Fatalf("expected default rate limit 120, got %d", cfg.RateLimitRequests)
	}
}

func TestLoadEnvironment(t *testing.T) {
	t.Setenv("APP_PORT", "9090")
	t.Setenv("APP_MAX_BODY_BYTES", "2048")
	t.Setenv("APP_READ_TIMEOUT", "2s")
	t.Setenv("APP_CORS_ALLOWED_ORIGINS", "https://example.com, https://app.example.com")

	cfg := Load()

	if cfg.Port != "9090" || cfg.MaxBodyBytes != 2048 || cfg.ReadTimeout != 2*time.Second {
		t.Fatalf("environment configuration was not loaded correctly: %+v", cfg)
	}
	if len(cfg.CORSAllowedOrigins) != 2 {
		t.Fatalf("expected two CORS origins, got %d", len(cfg.CORSAllowedOrigins))
	}
}

func TestProductionRequiresSecret(t *testing.T) {
	cfg := &Config{Environment: "production", Port: "8080", MaxBodyBytes: 1024, RateLimitRequests: 10, RateLimitWindow: time.Minute}
	if err := cfg.Validate(); err == nil {
		t.Fatal("expected production secret validation error")
	}

	cfg.SecretKey = "12345678901234567890123456789012"
	if err := cfg.Validate(); err != nil {
		t.Fatalf("expected valid production config, got %v", err)
	}
}

func TestWildcardCORSRejected(t *testing.T) {
	cfg := &Config{
		Environment: "development", Port: "8080", MaxBodyBytes: 1024,
		RateLimitRequests: 10, RateLimitWindow: time.Minute,
		CORSAllowedOrigins: []string{"*"},
	}
	if err := cfg.Validate(); err == nil {
		t.Fatal("expected wildcard CORS to be rejected")
	}
}
