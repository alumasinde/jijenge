package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Security/Models"
	"github.com/alumasinde/jijenge/Security/Repositories"
	"strings"
	"time"
)

var ErrInvalidEvent = errors.New("invalid security event")

type Service struct {
	Repo Repositories.Repository
	Now  func() time.Time
}

func New(r Repositories.Repository) *Service { return &Service{Repo: r, Now: time.Now} }
func (s *Service) Record(ctx context.Context, e *Models.Event) error {
	if e == nil || e.UserID == nil || strings.TrimSpace(e.EventType) == "" || len(e.EventType) > 64 {
		return ErrInvalidEvent
	}
	e.EventType = strings.TrimSpace(e.EventType)
	if e.CreatedAt.IsZero() {
		e.CreatedAt = s.Now()
	}
	return s.Repo.Record(ctx, e)
}
