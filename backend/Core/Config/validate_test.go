package Config

import "testing"

func TestProductionRequiresStrongSecret(t *testing.T) {
	c := &Config{Port: "8080", Environment: "production", SecretKey: "short", MaxBodyBytes: 1024,
		RateLimitRequests: 120, RateLimitWindow: 1, AuthRateLimitRequests: 10, AuthRateLimitWindow: 1}
	if err := c.Validate(); err != ErrProductionSecretMissing {
		t.Fatalf("expected secret error, got %v", err)
	}
}

func TestProductionRejectsWildcardCORS(t *testing.T) {
	c := &Config{Port: "8080", Environment: "production", SecretKey: "01234567890123456789012345678901",
		MaxBodyBytes: 1024, RateLimitRequests: 120, RateLimitWindow: 1, AuthRateLimitRequests: 10, AuthRateLimitWindow: 1,
		CORSAllowedOrigins: []string{"*"}}
	if err := c.Validate(); err == nil {
		t.Fatal("expected wildcard CORS to be rejected")
	}
}

func TestPaymentsRequireStrongWebhookSecretAndClearingAccount(t *testing.T) {
	c := &Config{
		Port: "8080", Environment: "production", SecretKey: "01234567890123456789012345678901",
		MaxBodyBytes: 1024, RateLimitRequests: 120, RateLimitWindow: 1,
		AuthRateLimitRequests: 10, AuthRateLimitWindow: 1,
		PaymentProviderName: "test", PaymentWebhookSecret: "short", PaymentClearingAccountID: 1,
	}
	if err := c.Validate(); err == nil {
		t.Fatal("expected weak payment webhook secret to fail")
	}
	c.PaymentWebhookSecret = "01234567890123456789012345678901"
	c.PaymentClearingAccountID = 0
	if err := c.Validate(); err == nil {
		t.Fatal("expected missing clearing account to fail")
	}
}
