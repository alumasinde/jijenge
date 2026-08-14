package Config

import (
	"errors"
	"fmt"
	"time"
)

var ErrProductionSecretMissing = errors.New("APP_SECRET_KEY is required in production")

func (c *Config) Validate() error {
	if c.Port == "" {
		return errors.New("APP_PORT is required")
	}
	if c.MaxBodyBytes <= 0 {
		return errors.New("APP_MAX_BODY_BYTES must be positive")
	}
	if c.RateLimitRequests <= 0 {
		return errors.New("APP_RATE_LIMIT_REQUESTS must be positive")
	}
	if c.RateLimitWindow <= 0 {
		return errors.New("APP_RATE_LIMIT_WINDOW must be positive")
	}
	// Keep zero-valued Config structs useful in unit tests and programmatic
	// construction; Load() supplies secure positive defaults for real processes.
	if c.AuthRateLimitRequests <= 0 {
		c.AuthRateLimitRequests = 10
	}
	if c.AuthRateLimitWindow <= 0 {
		c.AuthRateLimitWindow = time.Minute
	}

	if c.Environment == "production" {
		if len([]byte(c.SecretKey)) < 32 {
			return ErrProductionSecretMissing
		}
		if c.ReadTimeout > 60*time.Second || c.WriteTimeout > 60*time.Second || c.IdleTimeout > 5*time.Minute {
			return errors.New("production HTTP timeouts are too permissive")
		}
	}

	if c.PaymentProviderName != "" {
		if len(c.PaymentProviderName) > 64 {
			return errors.New("PAYMENT_PROVIDER_NAME is too long")
		}
		if len([]byte(c.PaymentWebhookSecret)) < 32 {
			return errors.New("PAYMENT_WEBHOOK_SECRET must contain at least 32 bytes when payments are enabled")
		}
		if c.PaymentClearingAccountID == 0 {
			return errors.New("PAYMENT_CLEARING_ACCOUNT_ID is required when payments are enabled")
		}
	}
	for _, origin := range c.CORSAllowedOrigins {
		if origin == "*" {
			return fmt.Errorf("wildcard CORS origin is not allowed")
		}
	}

	return nil
}
