package Routes

import (
	"context"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Auth/Handlers"
	AuthMiddleware "github.com/alumasinde/jijenge/Auth/Middleware"
	"github.com/alumasinde/jijenge/Auth/Repositories"
	"github.com/alumasinde/jijenge/Auth/Services"
	"github.com/alumasinde/jijenge/Core/Config"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Core/HTTP"
	"github.com/alumasinde/jijenge/Core/Logger"
	"github.com/alumasinde/jijenge/Core/Middleware"
	AuthorizationHandlers "github.com/alumasinde/jijenge/Authorization/Handlers"
	AuthorizationMiddleware "github.com/alumasinde/jijenge/Authorization/Middleware"
	AuthorizationRepositories "github.com/alumasinde/jijenge/Authorization/Repositories"
	AuthorizationServices "github.com/alumasinde/jijenge/Authorization/Services"
	EscrowHandlers "github.com/alumasinde/jijenge/Escrow/Handlers"
	EscrowRepositories "github.com/alumasinde/jijenge/Escrow/Repositories"
	EscrowServices "github.com/alumasinde/jijenge/Escrow/Services"
	FinancialRepositories "github.com/alumasinde/jijenge/Financial/Repositories"
	FinancialServices "github.com/alumasinde/jijenge/Financial/Services"
	PaymentHandlers "github.com/alumasinde/jijenge/Payments/Handlers"
	PaymentProvider "github.com/alumasinde/jijenge/Payments/Provider"
	PaymentRepositories "github.com/alumasinde/jijenge/Payments/Repositories"
	PaymentServices "github.com/alumasinde/jijenge/Payments/Services"
	RatingHandlers "github.com/alumasinde/jijenge/Ratings/Handlers"
	RatingRepositories "github.com/alumasinde/jijenge/Ratings/Repositories"
	RatingServices "github.com/alumasinde/jijenge/Ratings/Services"
	SettlementHandlers "github.com/alumasinde/jijenge/Settlements/Handlers"
	SettlementRepositories "github.com/alumasinde/jijenge/Settlements/Repositories"
	SettlementServices "github.com/alumasinde/jijenge/Settlements/Services"
	TaskHandlers "github.com/alumasinde/jijenge/Tasks/Handlers"
	TaskRepositories "github.com/alumasinde/jijenge/Tasks/Repositories"
	TaskServices "github.com/alumasinde/jijenge/Tasks/Services"
)

func Register(cfg *Config.Config, logger *Logger.Logger, databases ...*Database.DB) http.Handler {
	var db *Database.DB
	if len(databases) > 0 {
		db = databases[0]
	}
	mux := http.NewServeMux()

	mux.HandleFunc("GET /health", health)
	mux.HandleFunc("GET /ready", func(w http.ResponseWriter, r *http.Request) {
		ready(w, r, db)
	})

	// Phase 4 uses repositories behind interfaces. Database-backed repositories
	// are introduced after the authentication contract is finalized; the
	// in-memory implementation keeps the API executable and testable now.
	var userRepo Repositories.UserRepository = Repositories.NewMemoryUserRepository()
	var sessionRepo Repositories.SessionRepository = Repositories.NewMemorySessionRepository()
	var taskRepo TaskRepositories.TaskRepository = TaskRepositories.NewMemoryRepository()

	if db != nil {
		userRepo = Repositories.NewMySQLUserRepository(db)
		sessionRepo = Repositories.NewMySQLSessionRepository(db)
		taskRepo = TaskRepositories.NewMySQLRepository(db)
	}

	authService := Services.NewAuthService(userRepo, sessionRepo, Services.Config{})
	AuthHandler := Handlers.NewAuthHandler(authService)
	mux.HandleFunc("POST /api/v1/auth/register", AuthHandler.Register)
	mux.HandleFunc("POST /api/v1/auth/login", AuthHandler.Login)
	mux.HandleFunc("POST /api/v1/auth/refresh", AuthHandler.Refresh)
	mux.HandleFunc("POST /api/v1/auth/logout", AuthHandler.Logout)

	// A single Financial ledger service/repository is shared by anything
	// in this composition that needs to read or create accounts (currently:
	// registration account provisioning and the payments webhook), rather
	// than constructing a second independent repository per consumer.
	var ledgerService *FinancialServices.Service
	var ledgerRepo FinancialRepositories.LedgerRepository
	if db != nil {
		ledgerRepo = FinancialRepositories.NewMySQLRepository(db)
		ledgerService = FinancialServices.New(ledgerRepo)

		// Every new user gets a zero-balance ledger account in their
		// platform's default currency at registration time, so escrow
		// funding/release has an account to reference without any manual
		// database step. See AuthHandler.AccountProvisioner for the
		// failure-handling contract (best-effort, never fails registration).
		defaultCurrency := cfg.DefaultCurrency
		AuthHandler.SetAccountProvisioner(func(ctx context.Context, userID uint64) (uint64, error) {
			owner := userID
			account, err := ledgerService.CreateAccount(ctx, &owner, defaultCurrency)
			if err != nil {
				return 0, err
			}
			return account.ID, nil
		})
	}

	if db != nil && cfg.PaymentProviderName != "" {
		verifier, err := PaymentProvider.NewHMACSHA256Verifier(cfg.PaymentProviderName, []byte(cfg.PaymentWebhookSecret))
		if err != nil {
			panic(err)
		}
		paymentRepo := PaymentRepositories.NewMySQLRepository(db)
		paymentService := PaymentServices.New(paymentRepo, ledgerRepo, verifier)
		paymentService.SetClearingAccountID(cfg.PaymentClearingAccountID)
		paymentHandler := PaymentHandlers.NewWebhookHandler(paymentService, cfg.MaxBodyBytes)
		mux.HandleFunc("POST /api/v1/payments/webhook", paymentHandler.Handle)
	}

	// Authentication endpoints get a much tighter limiter than ordinary API
	// traffic to reduce credential stuffing, password spraying, and refresh-token
	// abuse. The key includes the route so one noisy endpoint cannot exhaust the
	// allowance of the others.

	// Phase 6 core task API. Production composition will inject MySQL repositories.
	taskService := TaskServices.New(taskRepo)
	taskHandler := TaskHandlers.New(taskService)
	authn := &AuthMiddleware.Authenticator{Service: authService}
	if db != nil {
		escrowRepo := EscrowRepositories.NewMySQLRepository(db)
		escrowService := EscrowServices.New(escrowRepo)
		taskHandler.SetEscrow(escrowService)
		escrowHandler := EscrowHandlers.New(escrowService)
		mux.Handle("POST /api/v1/escrows", authn.Require(http.HandlerFunc(escrowHandler.Fund)))
		mux.Handle("POST /api/v1/escrows/{id}/dispute", authn.Require(http.HandlerFunc(escrowHandler.Dispute)))
	}

	// Authorization (RBAC) management. These endpoints can create roles and
	// permissions, so they are gated behind authentication AND the
	// "authorization.manage" permission -- never exposed unauthenticated.
	// This was previously dead code: Authorization/routes.go defined a
	// RegisterRoutes function that nothing in the application ever called,
	// so /api/v1/authorization/* did not exist at runtime despite the
	// handler, service, and MySQL repository all being fully implemented
	// and tested.
	//
	// Bootstrap note: a fresh database has no roles/permissions/grants at
	// all, so nobody can satisfy "authorization.manage" yet. Operators must
	// seed the first permission, role, and grant directly via SQL (or a
	// trusted internal script) before these endpoints can be used to manage
	// authorization going forward. This mirrors how task_categories must
	// also be seeded before tasks can be created -- see the README.
	if db != nil {
		authzRepo := AuthorizationRepositories.NewMySQLAuthorizationRepository(db)
		authzService := AuthorizationServices.NewAuthorizationService(authzRepo)
		authzHandler := AuthorizationHandlers.New(authzService)
		permission := AuthorizationMiddleware.NewPermissionMiddleware(authzService)
		mux.Handle("POST /api/v1/authorization/roles",
			authn.Require(permission.Require("authorization.manage", http.HandlerFunc(authzHandler.CreateRole))))
		mux.Handle("POST /api/v1/authorization/permissions",
			authn.Require(permission.Require("authorization.manage", http.HandlerFunc(authzHandler.CreatePermission))))
	}
	if db != nil {
		settlementRepo := SettlementRepositories.NewMySQLRepository(db)
		settlementHandler := SettlementHandlers.New(SettlementServices.New(settlementRepo))
		mux.Handle("POST /api/v1/settlements", authn.Require(http.HandlerFunc(settlementHandler.Create)))
		mux.Handle("POST /api/v1/settlements/{id}/claim", authn.Require(http.HandlerFunc(settlementHandler.Claim)))
		mux.Handle("POST /api/v1/settlements/{id}/confirm", authn.Require(http.HandlerFunc(settlementHandler.Confirm)))
		mux.Handle("POST /api/v1/settlements/{id}/dispute", authn.Require(http.HandlerFunc(settlementHandler.Dispute)))
	}
	if db != nil {
		ratingRepo := RatingRepositories.NewMySQLRepository(db)
		ratingHandler := RatingHandlers.New(RatingServices.New(ratingRepo))
		mux.Handle("POST /api/v1/assignments/{id}/ratings", authn.Require(http.HandlerFunc(ratingHandler.Create)))
		mux.HandleFunc("GET /api/v1/users/{id}/rating", ratingHandler.Average)
	}
	mux.Handle("POST /api/v1/tasks", authn.Require(http.HandlerFunc(taskHandler.Create)))
	mux.Handle("POST /api/v1/tasks/{id}/publish", authn.Require(http.HandlerFunc(taskHandler.Publish)))
	mux.Handle("POST /api/v1/tasks/{id}/applications", authn.Require(http.HandlerFunc(taskHandler.Apply)))
	mux.Handle("POST /api/v1/tasks/{id}/start", authn.Require(http.HandlerFunc(taskHandler.Start)))
	mux.Handle("POST /api/v1/tasks/{id}/complete", authn.Require(http.HandlerFunc(taskHandler.Complete)))
	mux.Handle("POST /api/v1/tasks/{id}/cancel", authn.Require(http.HandlerFunc(taskHandler.Cancel)))
	mux.Handle("POST /api/v1/applications/{id}/accept", authn.Require(http.HandlerFunc(taskHandler.AcceptApplication)))
	mux.Handle("POST /api/v1/assignments/{id}/submit", authn.Require(http.HandlerFunc(taskHandler.Submit)))
	mux.Handle("POST /api/v1/assignments/{id}/verify", authn.Require(http.HandlerFunc(taskHandler.Verify)))
	mux.Handle("POST /api/v1/assignments/{id}/release", authn.Require(http.HandlerFunc(taskHandler.Release)))

	var handler http.Handler = mux

	limiter := Middleware.NewRateLimiter(cfg.RateLimitRequests, cfg.RateLimitWindow, 50_000)
	authLimiter := Middleware.NewRateLimiter(cfg.AuthRateLimitRequests, cfg.AuthRateLimitWindow, 50_000)
	handler = Middleware.RateLimit(limiter, func(r *http.Request) string {
		host, _, err := net.SplitHostPort(r.RemoteAddr)
		if err == nil {
			return host
		}
		return r.RemoteAddr
	})(handler)
	// Authentication-specific limiter is deliberately applied after the global
	// limiter and before handlers. This keeps login/refresh/logout/register
	// protected even when ordinary API traffic has a higher allowance.
	handler = Middleware.ConditionalRateLimit(authLimiter, func(r *http.Request) string {
		if !strings.HasPrefix(r.URL.Path, "/api/v1/auth/") {
			return ""
		}
		host, _, err := net.SplitHostPort(r.RemoteAddr)
		if err != nil {
			host = r.RemoteAddr
		}
		return host + "|" + r.URL.Path
	})(handler)

	if len(cfg.CORSAllowedOrigins) > 0 {
		handler = Middleware.NewCORS(cfg.CORSAllowedOrigins).Handler(handler)
	}

	handler = Middleware.SecurityHeaders(strings.EqualFold(cfg.Environment, "production"))(handler)
	handler = Middleware.BodyLimit(cfg.MaxBodyBytes)(handler)
	handler = Middleware.Timeout(cfg.WriteTimeout)(handler)
	handler = Middleware.RequestID(handler)
	handler = Middleware.Recovery(logger.Logger)(handler)

	return handler
}

func health(w http.ResponseWriter, r *http.Request) {
	HTTP.JSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func ready(w http.ResponseWriter, r *http.Request, db *Database.DB) {
	if db != nil {
		ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()
		if err := db.PingContext(ctx); err != nil {
			HTTP.JSON(w, http.StatusServiceUnavailable, map[string]string{"status": "not_ready"})
			return
		}
	}
	HTTP.JSON(w, http.StatusOK, map[string]string{"status": "ready"})
}
