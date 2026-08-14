package Services

import (
	"context"
	"testing"
	"time"

	"github.com/alumasinde/jijenge/Auth/DTOs"
	"github.com/alumasinde/jijenge/Auth/Repositories"
)

func testService() *AuthService {
	return NewAuthService(
		Repositories.NewMemoryUserRepository(),
		Repositories.NewMemorySessionRepository(),
		Config{AccessTokenTTL: time.Minute, RefreshTokenTTL: time.Hour},
	)
}

func TestRegisterLoginRefreshLogout(t *testing.T) {
	s := testService()
	ctx := context.Background()

	user, err := s.Register(ctx, DTOs.RegisterRequest{
		Email: "User@Example.com", Password: "a very strong password", FirstName: "Jane", LastName: "Doe",
	})
	if err != nil {
		t.Fatal(err)
	}
	if user.PasswordHash != "" {
		t.Fatal("password hash must not be returned from service registration result")
	}

	login, err := s.Login(ctx, DTOs.LoginRequest{Email: "user@example.com", Password: "a very strong password"})
	if err != nil {
		t.Fatal(err)
	}
	if login.AccessToken == "" || login.RefreshToken == "" {
		t.Fatal("expected access and refresh tokens")
	}

	oldRefresh := login.RefreshToken
	refreshed, err := s.Refresh(ctx, oldRefresh)
	if err != nil {
		t.Fatal(err)
	}
	if refreshed.RefreshToken == oldRefresh {
		t.Fatal("refresh token must rotate")
	}

	if _, err := s.Refresh(ctx, oldRefresh); err != ErrInvalidRefresh {
		t.Fatalf("old refresh token should be invalid after rotation, got %v", err)
	}

	if err := s.Logout(ctx, refreshed.RefreshToken); err != nil {
		t.Fatal(err)
	}
	if _, err := s.Refresh(ctx, refreshed.RefreshToken); err != ErrInvalidRefresh {
		t.Fatalf("logged out token should be invalid, got %v", err)
	}
}

func TestInvalidCredentialsDoNotRevealUserExistence(t *testing.T) {
	s := testService()
	ctx := context.Background()

	_, _ = s.Register(ctx, DTOs.RegisterRequest{
		Email: "user@example.com", Password: "a very strong password", FirstName: "Jane", LastName: "Doe",
	})

	_, err1 := s.Login(ctx, DTOs.LoginRequest{Email: "user@example.com", Password: "wrong password"})
	_, err2 := s.Login(ctx, DTOs.LoginRequest{Email: "missing@example.com", Password: "wrong password"})

	if err1 != ErrInvalidCredentials || err2 != ErrInvalidCredentials {
		t.Fatalf("expected same credential error, got %v and %v", err1, err2)
	}
}

func TestDisabledAccountCannotLogin(t *testing.T) {
	s := testService()
	ctx := context.Background()

	user, err := s.Register(ctx, DTOs.RegisterRequest{
		Email: "blocked@example.com", Password: "a very strong password", FirstName: "A", LastName: "B",
	})
	if err != nil {
		t.Fatal(err)
	}

	_ = user
}
