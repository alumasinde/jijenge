package Services

import (
	"context"
	"errors"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Core/Security"
	"github.com/alumasinde/jijenge/Financial/Models"
	"github.com/alumasinde/jijenge/Financial/Repositories"
)

var ErrInvalidCurrency = errors.New("invalid currency")

type Service struct {
	Repo Repositories.LedgerRepository
	Now  func() time.Time
}

func New(repo Repositories.LedgerRepository) *Service { return &Service{Repo: repo, Now: time.Now} }
func (s *Service) CreateAccount(ctx context.Context, owner *uint64, currency string) (*Models.Account, error) {
	currency = strings.ToUpper(strings.TrimSpace(currency))
	if len(currency) != 3 {
		return nil, ErrInvalidCurrency
	}
	a := &Models.Account{PublicID: token(), OwnerUserID: owner, Currency: currency, Status: Models.AccountActive, CreatedAt: s.Now()}
	if err := s.Repo.CreateAccount(ctx, a); err != nil {
		return nil, err
	}
	return a, nil
}
func (s *Service) Transfer(ctx context.Context, idempotencyKey, description string, from, to uint64, amount int64) (*Models.Transaction, error) {
	if strings.TrimSpace(idempotencyKey) == "" || len(idempotencyKey) > 128 || strings.TrimSpace(description) == "" || len(description) > 500 {
		return nil, errors.New("invalid transfer request")
	}
	if amount <= 0 {
		return nil, Repositories.ErrInvalidAmount
	}
	return s.Repo.Transfer(ctx, idempotencyKey, token(), strings.TrimSpace(description), from, to, amount, s.Now())
}
func (s *Service) PlaceHold(ctx context.Context, idempotencyKey, reference string, account uint64, amount int64) (*Models.Hold, error) {
	if strings.TrimSpace(idempotencyKey) == "" || len(idempotencyKey) > 128 || strings.TrimSpace(reference) == "" || len(reference) > 128 {
		return nil, errors.New("invalid hold request")
	}
	if amount <= 0 {
		return nil, Repositories.ErrInvalidAmount
	}
	return s.Repo.CreateHold(ctx, idempotencyKey, strings.TrimSpace(reference), account, amount, s.Now())
}
func (s *Service) ReleaseHold(ctx context.Context, id uint64) error {
	if id == 0 {
		return Repositories.ErrHoldNotFound
	}
	return s.Repo.ReleaseHold(ctx, id, s.Now())
}
func (s *Service) CaptureHold(ctx context.Context, id, to uint64, amount int64) error {
	if id == 0 || to == 0 {
		return Repositories.ErrHoldNotFound
	}
	return s.Repo.CaptureHold(ctx, id, to, amount, s.Now())
}
func token() string {
	b, err := Security.GenerateToken(32)
	if err != nil {
		panic(err)
	}
	return b[:26]
}
