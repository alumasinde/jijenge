package Middleware

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/alumasinde/jijenge/Auth/DTOs"
	"github.com/alumasinde/jijenge/Auth/Repositories"
	"github.com/alumasinde/jijenge/Auth/Services"
)

func TestRequireAuthentication(t *testing.T) {
	users := Repositories.NewMemoryUserRepository()
	sessions := Repositories.NewMemorySessionRepository()
	service := Services.NewAuthService(users, sessions, Services.Config{AccessTokenTTL: time.Minute, RefreshTokenTTL: time.Hour})

	login, err := func() (*DTOs.LoginResponse, error) {
		_, err := service.Register(context.Background(), DTOs.RegisterRequest{
			Email: "a@example.com", Password: "a very strong password", FirstName: "A", LastName: "B",
		})
		if err != nil {
			return nil, err
		}
		return service.Login(context.Background(), DTOs.LoginRequest{Email: "a@example.com", Password: "a very strong password"})
	}()
	if err != nil {
		t.Fatal(err)
	}

	auth := (&Authenticator{Service: service}).Require(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if _, ok := UserID(r.Context()); !ok {
			t.Fatal("expected user ID")
		}
		w.WriteHeader(http.StatusNoContent)
	}))

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer "+login.AccessToken)
	rec := httptest.NewRecorder()
	auth.ServeHTTP(rec, req)
	if rec.Code != http.StatusNoContent {
		t.Fatalf("expected 204, got %d", rec.Code)
	}
}
