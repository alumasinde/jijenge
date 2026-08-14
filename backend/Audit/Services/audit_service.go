package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Audit/Models"
	"github.com/alumasinde/jijenge/Audit/Repositories"
	"strings"
	"time"
)

var ErrInvalidAudit = errors.New("invalid audit event")

type Service struct {
	Repo Repositories.Repository
	Now  func() time.Time
}

func New(r Repositories.Repository) *Service { return &Service{Repo: r, Now: time.Now} }
func (s *Service) Record(ctx context.Context, e *Models.AuditEvent) error {
	if e == nil || strings.TrimSpace(e.Action) == "" || strings.TrimSpace(e.ResourceType) == "" || len(e.Action) > 64 || len(e.ResourceType) > 64 || len(e.Reason) > 500 {
		return ErrInvalidAudit
	}
	e.Action = strings.TrimSpace(e.Action)
	e.ResourceType = strings.TrimSpace(e.ResourceType)
	if e.CreatedAt.IsZero() {
		e.CreatedAt = s.Now()
	}
	if e.Outcome == "" {
		e.Outcome = "success"
	}
	return s.Repo.Record(ctx, e)
}
func (s *Service) StartRun(ctx context.Context) *Models.ReconciliationRun {
	return &Models.ReconciliationRun{Status: "running", StartedAt: s.Now()}
}

func (s *Service) VerifyChain(ctx context.Context) error {
	return s.Repo.VerifyChain(ctx)
}
