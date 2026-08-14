package Config

import (
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	AppName                  string
	Environment              string
	Host                     string
	Port                     string
	ReadTimeout              time.Duration
	WriteTimeout             time.Duration
	IdleTimeout              time.Duration
	ShutdownTimeout          time.Duration
	MaxBodyBytes             int64
	RateLimitRequests        int
	RateLimitWindow          time.Duration
	AuthRateLimitRequests    int
	AuthRateLimitWindow      time.Duration
	CORSAllowedOrigins       []string
	SecretKey                string
	DBDriver                 string
	DBDSN                    string
	DBMaxOpenConns           int
	DBMaxIdleConns           int
	DBConnMaxLifetime        time.Duration
	DBConnMaxIdleTime        time.Duration
	PaymentProviderName      string
	PaymentWebhookSecret     string
	PaymentClearingAccountID uint64
	DefaultCurrency          string
}

func Load() *Config {
	return &Config{
		AppName:                  getEnv("APP_NAME", "Jijenge"),
		Environment:              getEnv("APP_ENV", "development"),
		Host:                     getEnv("APP_HOST", "0.0.0.0"),
		Port:                     getEnv("APP_PORT", "8080"),
		ReadTimeout:              getDuration("APP_READ_TIMEOUT", 10*time.Second),
		WriteTimeout:             getDuration("APP_WRITE_TIMEOUT", 15*time.Second),
		IdleTimeout:              getDuration("APP_IDLE_TIMEOUT", 60*time.Second),
		ShutdownTimeout:          getDuration("APP_SHUTDOWN_TIMEOUT", 15*time.Second),
		MaxBodyBytes:             getInt64("APP_MAX_BODY_BYTES", 1<<20),
		RateLimitRequests:        getInt("APP_RATE_LIMIT_REQUESTS", 120),
		RateLimitWindow:          getDuration("APP_RATE_LIMIT_WINDOW", time.Minute),
		CORSAllowedOrigins:       getList("APP_CORS_ALLOWED_ORIGINS"),
		SecretKey:                os.Getenv("APP_SECRET_KEY"),
		DBDriver:                 getEnv("DB_DRIVER", "mysql"),
		DBDSN:                    os.Getenv("DB_DSN"),
		DBMaxOpenConns:           getInt("DB_MAX_OPEN_CONNS", 10),
		DBMaxIdleConns:           getInt("DB_MAX_IDLE_CONNS", 5),
		DBConnMaxLifetime:        getDuration("DB_CONN_MAX_LIFETIME", 30*time.Minute),
		DBConnMaxIdleTime:        getDuration("DB_CONN_MAX_IDLE_TIME", 5*time.Minute),
		PaymentProviderName:      strings.TrimSpace(os.Getenv("PAYMENT_PROVIDER_NAME")),
		PaymentWebhookSecret:     os.Getenv("PAYMENT_WEBHOOK_SECRET"),
		PaymentClearingAccountID: uint64(getInt64("PAYMENT_CLEARING_ACCOUNT_ID", 0)),
		DefaultCurrency:          strings.ToUpper(getEnv("APP_DEFAULT_CURRENCY", "KES")),
	}
}

func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func getDuration(key string, fallback time.Duration) time.Duration {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	duration, err := time.ParseDuration(value)
	if err != nil || duration <= 0 {
		return fallback
	}
	return duration
}

func getInt(key string, fallback int) int {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	result, err := strconv.Atoi(value)
	if err != nil || result <= 0 {
		return fallback
	}
	return result
}

func getList(key string) []string {
	value := os.Getenv(key)
	if value == "" {
		return nil
	}
	parts := strings.Split(value, ",")
	result := make([]string, 0, len(parts))
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part != "" {
			result = append(result, part)
		}
	}
	return result
}

func getInt64(key string, fallback int64) int64 {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	result, err := strconv.ParseInt(value, 10, 64)
	if err != nil || result <= 0 {
		return fallback
	}
	return result
}
