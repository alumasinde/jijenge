package Services

import (
	"context"
	"errors"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Auth/DTOs"
	"github.com/alumasinde/jijenge/Auth/Models"
	"github.com/alumasinde/jijenge/Auth/Repositories"
	"github.com/alumasinde/jijenge/Core/Security"
	"github.com/alumasinde/jijenge/Core/Validation"
)

var (
	ErrInvalidCredentials = errors.New("invalid credentials")
	ErrAccountDisabled    = errors.New("account is not active")
	ErrInvalidRefresh     = errors.New("invalid refresh token")
)

type Config struct {
	AccessTokenTTL     time.Duration
	RefreshTokenTTL    time.Duration
	MaxSessionLifetime time.Duration
}

type AuthService struct {
	Users    Repositories.UserRepository
	Sessions Repositories.SessionRepository
	Config   Config
	Now      func() time.Time
}

func NewAuthService(users Repositories.UserRepository, sessions Repositories.SessionRepository, cfg Config) *AuthService {
	if cfg.AccessTokenTTL <= 0 {
		cfg.AccessTokenTTL = 15 * time.Minute
	}
	if cfg.RefreshTokenTTL <= 0 {
		cfg.RefreshTokenTTL = 30 * 24 * time.Hour
	}
	if cfg.MaxSessionLifetime <= 0 {
		cfg.MaxSessionLifetime = 90 * 24 * time.Hour
	}
	return &AuthService{Users: users, Sessions: sessions, Config: cfg, Now: time.Now}
}

func (s *AuthService) Register(ctx context.Context, req DTOs.RegisterRequest) (*Models.User, error) {
	email := strings.ToLower(strings.TrimSpace(req.Email))
	if err := Validation.Email(email); err != nil {
		return nil, err
	}
	if err := Validation.Password(req.Password); err != nil {
		return nil, err
	}
	if err := Validation.Required(req.FirstName, "first_name"); err != nil {
		return nil, err
	}
	if err := Validation.Required(req.LastName, "last_name"); err != nil {
		return nil, err
	}

	hash, err := Security.HashPassword(req.Password)
	if err != nil {
		return nil, err
	}

	user := &Models.User{
		PublicID:     newPublicID(),
		Email:        email,
		PasswordHash: hash,
		Status:       Models.StatusActive,
		CreatedAt:    s.Now(),
		UpdatedAt:    s.Now(),
	}
	if err := s.Users.Create(ctx, user); err != nil {
		return nil, err
	}
	user.PasswordHash = ""
	return user, nil
}

func (s *AuthService) Login(ctx context.Context, req DTOs.LoginRequest) (*DTOs.LoginResponse, error) {
	email := strings.ToLower(strings.TrimSpace(req.Email))
	user, err := s.Users.FindByEmail(ctx, email)
	if err != nil {
		return nil, ErrInvalidCredentials
	}

	valid, verifyErr := Security.VerifyPassword(req.Password, user.PasswordHash)
	if verifyErr != nil || !valid {
		return nil, ErrInvalidCredentials
	}
	if user.Status != Models.StatusActive {
		return nil, ErrAccountDisabled
	}

	access, err := Security.GenerateToken(32)
	if err != nil {
		return nil, err
	}
	refresh, err := Security.GenerateToken(64)
	if err != nil {
		return nil, err
	}

	now := s.Now()
	session := &Models.Session{
		UserID:          user.ID,
		AccessTokenHash: Security.HashToken(access),
		TokenHash:       Security.HashToken(refresh),
		ExpiresAt:       now.Add(s.Config.RefreshTokenTTL),
		CreatedAt:       now,
		LastSeenAt:      &now,
	}
	if err := s.Sessions.Create(ctx, session); err != nil {
		return nil, err
	}

	return &DTOs.LoginResponse{
		AccessToken:  access,
		RefreshToken: refresh,
		TokenType:    "Bearer",
		ExpiresIn:    int64(s.Config.AccessTokenTTL.Seconds()),
	}, nil
}

func (s *AuthService) Refresh(ctx context.Context, refreshToken string) (*DTOs.LoginResponse, error) {
	if strings.TrimSpace(refreshToken) == "" {
		return nil, ErrInvalidRefresh
	}
	hash := Security.HashToken(refreshToken)
	now := s.Now()

	session, err := s.Sessions.FindActiveByTokenHash(ctx, hash, now)
	if err != nil {
		return nil, ErrInvalidRefresh
	}

	user, err := s.Users.FindByID(ctx, session.UserID)
	if err != nil || user.Status != Models.StatusActive {
		return nil, ErrInvalidRefresh
	}

	if now.After(session.CreatedAt.Add(s.Config.MaxSessionLifetime)) {
		return nil, ErrInvalidRefresh
	}

	newAccess, err := Security.GenerateToken(32)
	if err != nil {
		return nil, err
	}
	newRefresh, err := Security.GenerateToken(64)
	if err != nil {
		return nil, err
	}

	newSession := &Models.Session{
		UserID:          user.ID,
		AccessTokenHash: Security.HashToken(newAccess),
		TokenHash:       Security.HashToken(newRefresh),
		ExpiresAt:       now.Add(s.Config.RefreshTokenTTL),
		CreatedAt:       now,
		LastSeenAt:      &now,
	}
	if err := s.Sessions.RotateRefresh(ctx, session.ID, newSession, now); err != nil {
		return nil, err
	}

	return &DTOs.LoginResponse{
		AccessToken:  newAccess,
		RefreshToken: newRefresh,
		TokenType:    "Bearer",
		ExpiresIn:    int64(s.Config.AccessTokenTTL.Seconds()),
	}, nil
}

func (s *AuthService) Logout(ctx context.Context, refreshToken string) error {
	if strings.TrimSpace(refreshToken) == "" {
		return nil
	}
	hash := Security.HashToken(refreshToken)
	session, err := s.Sessions.FindActiveByTokenHash(ctx, hash, s.Now())
	if errors.Is(err, Repositories.ErrSessionNotFound) {
		return nil
	}
	if err != nil {
		return err
	}
	return s.Sessions.Revoke(ctx, session.ID, s.Now())
}

func (s *AuthService) LogoutAll(ctx context.Context, userID uint64) error {
	return s.Sessions.RevokeAllForUser(ctx, userID, s.Now())
}

func (s *AuthService) AuthenticateAccessToken(ctx context.Context, accessToken string) (*Models.User, *Models.Session, error) {
	if strings.TrimSpace(accessToken) == "" {
		return nil, nil, ErrInvalidCredentials
	}
	hash := Security.HashToken(accessToken)
	session, err := s.Sessions.FindActiveByAccessTokenHash(ctx, hash, s.Now())
	if err != nil {
		return nil, nil, ErrInvalidCredentials
	}
	user, err := s.Users.FindByID(ctx, session.UserID)
	if err != nil || user.Status != Models.StatusActive {
		return nil, nil, ErrInvalidCredentials
	}
	return user, session, nil
}

func newPublicID() string {
	token, err := Security.GenerateToken(32)
	if err != nil {
		panic(err)
	}
	return token[:26]
}
