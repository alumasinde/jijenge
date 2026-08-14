package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Admin/Models"
	"github.com/alumasinde/jijenge/Admin/Repositories"
	"strings"
	"time"
)

var ErrInvalid = errors.New("invalid admin request")

type Service struct {
	Repo Repositories.Repository
	Now  func() time.Time
}

func New(r Repositories.Repository) *Service { return &Service{Repo: r, Now: time.Now} }
func (s *Service) Request(ctx context.Context, a Models.ActionType, target, admin uint64, reason string) (*Models.ActionRequest, error) {
	reason = strings.TrimSpace(reason)
	if target == 0 || admin == 0 || reason == "" || len(reason) > 500 {
		return nil, ErrInvalid
	}
	switch a {
	case Models.BlockUser, Models.UnblockUser, Models.FreezeAccount, Models.UnfreezeAccount:
	default:
		return nil, ErrInvalid
	}
	x := &Models.ActionRequest{Action: a, TargetID: target, RequestedBy: admin, Reason: reason, CreatedAt: s.Now()}
	if e := s.Repo.CreateRequest(ctx, x); e != nil {
		return nil, e
	}
	return x, nil
}
func (s *Service) Approve(ctx context.Context, id, admin uint64) error {
	if id == 0 || admin == 0 {
		return ErrInvalid
	}
	return s.Repo.ApproveAndExecute(ctx, id, admin, s.Now())
}
func (s *Service) Reject(ctx context.Context, id, admin uint64) error {
	if id == 0 || admin == 0 {
		return ErrInvalid
	}
	return s.Repo.Reject(ctx, id, admin, s.Now())
}
