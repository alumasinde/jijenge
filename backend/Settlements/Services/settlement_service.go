package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Core/Security"
	"github.com/alumasinde/jijenge/Settlements/Models"
	"github.com/alumasinde/jijenge/Settlements/Repositories"
	"strings"
	"time"
)

var ErrInvalid = errors.New("invalid settlement")

type Service struct {
	Repo Repositories.Repository
	Now  func() time.Time
}

func New(r Repositories.Repository) *Service { return &Service{Repo: r, Now: time.Now} }
func (s *Service) Create(ctx context.Context, task, assignment, payer, payee uint64, method Models.Method, amount int64, currency string) (*Models.Settlement, error) {
	currency = strings.ToUpper(strings.TrimSpace(currency))
	switch method {
	case Models.Platform, Models.Cash, Models.MobileMoney, Models.BankTransfer, Models.Other:
	default:
		return nil, ErrInvalid
	}
	if task == 0 || assignment == 0 || payer == 0 || payee == 0 || amount <= 0 || payer == payee || len(currency) != 3 {
		return nil, ErrInvalid
	}
	b, e := Security.GenerateToken(32)
	if e != nil {
		return nil, e
	}
	x := &Models.Settlement{PublicID: b[:26], TaskID: task, AssignmentID: assignment, PayerUserID: payer, PayeeUserID: payee, Method: method, AmountCents: amount, Currency: currency, CreatedAt: s.Now(), UpdatedAt: s.Now()}
	if e = s.Repo.Create(ctx, x); e != nil {
		return nil, e
	}
	return x, nil
}
func (s *Service) Claim(ctx context.Context, id, user uint64) error {
	return s.Repo.Claim(ctx, id, user, s.Now())
}
func (s *Service) Confirm(ctx context.Context, id, user uint64) error {
	return s.Repo.Confirm(ctx, id, user, s.Now())
}
func (s *Service) Dispute(ctx context.Context, id, user uint64) error {
	return s.Repo.Dispute(ctx, id, user, s.Now())
}

func (s *Service) CreateManualForUser(ctx context.Context, task, assignment, payer, payee, requester uint64, method Models.Method, amount int64, currency, evidence, idempotencyKey string) (*Models.Settlement, error) {
	if requester == 0 || payer != requester || task == 0 || assignment == 0 || payer == 0 || payee == 0 || payer == payee || amount <= 0 || method == Models.Platform {
		return nil, ErrInvalid
	}
	currency = strings.ToUpper(strings.TrimSpace(currency))
	evidence = strings.TrimSpace(evidence)
	if len(currency) != 3 || evidence == "" || len(evidence) > 255 || len(strings.TrimSpace(idempotencyKey)) < 16 || len(strings.TrimSpace(idempotencyKey)) > 128 {
		return nil, ErrInvalid
	}
	switch method {
	case Models.Cash, Models.MobileMoney, Models.BankTransfer, Models.Other:
	default:
		return nil, ErrInvalid
	}
	b, err := Security.GenerateToken(32)
	if err != nil {
		return nil, err
	}
	now := s.Now()
	x := &Models.Settlement{PublicID: b[:26], TaskID: task, AssignmentID: assignment, PayerUserID: payer, PayeeUserID: payee, Method: method, AmountCents: amount, Currency: currency, EvidenceReference: evidence, IdempotencyKey: strings.TrimSpace(idempotencyKey), CreatedAt: now, UpdatedAt: now}
	if err = s.Repo.CreateForUser(ctx, x, requester); err != nil {
		return nil, err
	}
	return x, nil
}
func (s *Service) ConfirmWithNote(ctx context.Context, id, user uint64, note string) error {
	if id == 0 || user == 0 {
		return ErrInvalid
	}
	return s.Repo.ConfirmWithNote(ctx, id, user, note, s.Now())
}
func (s *Service) DisputeWithReason(ctx context.Context, id, user uint64, reason string) error {
	if id == 0 || user == 0 {
		return ErrInvalid
	}
	return s.Repo.DisputeWithReason(ctx, id, user, reason, s.Now())
}
