package Services

import (
	"context"
	"errors"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Escrow/Models"
	"github.com/alumasinde/jijenge/Escrow/Repositories"
)

var ErrInvalidEscrow = errors.New("invalid escrow request")

type Service struct {
	Repo Repositories.Repository
	Now  func() time.Time
}

func New(repo Repositories.Repository) *Service { return &Service{Repo: repo, Now: time.Now} }
func (s *Service) Fund(ctx context.Context, e *Models.Escrow) error {
	if e == nil || e.TaskID == 0 || e.AssignmentID == 0 || e.PayerAccountID == 0 || e.WorkerAccountID == 0 || e.AmountCents <= 0 || len(e.Currency) != 3 {
		return ErrInvalidEscrow
	}
	e.Currency = strings.ToUpper(strings.TrimSpace(e.Currency))
	return s.Repo.CreateAndFund(ctx, e)
}
func (s *Service) Submit(ctx context.Context, id uint64) error {
	if id == 0 {
		return ErrInvalidEscrow
	}
	return s.Repo.MarkSubmitted(ctx, id, s.Now())
}
func (s *Service) VerifyAndRelease(ctx context.Context, id uint64) error {
	if id == 0 {
		return ErrInvalidEscrow
	}
	return s.Repo.Release(ctx, id, s.Now())
}
func (s *Service) VerifyAndReleaseWithFee(ctx context.Context, id, feeCents, feeAccount uint64) error {
	if id == 0 || feeAccount == 0 && feeCents > 0 {
		return ErrInvalidEscrow
	}
	return s.Repo.ReleaseWithFee(ctx, id, int64(feeCents), feeAccount, s.Now())
}
func (s *Service) Refund(ctx context.Context, id uint64) error {
	if id == 0 {
		return ErrInvalidEscrow
	}
	return s.Repo.Refund(ctx, id, s.Now())
}
func (s *Service) Dispute(ctx context.Context, id, user uint64, reason string) (*Repositories.Dispute, error) {
	if id == 0 || user == 0 || len(strings.TrimSpace(reason)) < 5 || len(reason) > 2000 {
		return nil, ErrInvalidEscrow
	}
	return s.Repo.OpenDispute(ctx, id, user, strings.TrimSpace(reason), s.Now())
}
func (s *Service) ResolveDispute(ctx context.Context, disputeID uint64, res Repositories.DisputeResolution, workerCents, feeAccount uint64) error {
	if disputeID == 0 {
		return ErrInvalidEscrow
	}
	return s.Repo.ResolveDispute(ctx, disputeID, res, int64(workerCents), feeAccount, s.Now())
}

func (s *Service) SubmitAssignment(ctx context.Context, assignmentID uint64) error {
	if assignmentID == 0 {
		return ErrInvalidEscrow
	}
	return s.Repo.SubmitAssignment(ctx, assignmentID, s.Now())
}
func (s *Service) ReleaseVerifiedAssignment(ctx context.Context, assignmentID uint64) error {
	if assignmentID == 0 {
		return ErrInvalidEscrow
	}
	return s.Repo.ReleaseVerifiedAssignment(ctx, assignmentID, s.Now())
}

func (s *Service) FundForUser(ctx context.Context, e *Models.Escrow, userID uint64) error {
	if e == nil || userID == 0 || len(e.IdempotencyKey) < 16 || len(e.IdempotencyKey) > 128 || e.TaskID == 0 || e.AssignmentID == 0 || e.PayerAccountID == 0 || e.WorkerAccountID == 0 || e.AmountCents <= 0 || len(strings.TrimSpace(e.Currency)) != 3 {
		return ErrInvalidEscrow
	}
	e.Currency = strings.ToUpper(strings.TrimSpace(e.Currency))
	return s.Repo.CreateAndFundForUser(ctx, e, userID)
}

func (s *Service) ReleaseVerifiedAssignmentForUser(ctx context.Context, assignmentID, userID uint64) error {
	if assignmentID == 0 || userID == 0 {
		return ErrInvalidEscrow
	}
	return s.Repo.ReleaseVerifiedAssignmentForUser(ctx, assignmentID, userID, s.Now())
}
