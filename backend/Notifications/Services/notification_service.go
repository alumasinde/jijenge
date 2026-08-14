package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Notifications/Models"
	"github.com/alumasinde/jijenge/Notifications/Repositories"
	"strings"
	"time"
)

var ErrInvalidNotification = errors.New("invalid notification")

type Service struct {
	Repo Repositories.Repository
	Now  func() time.Time
}

func New(r Repositories.Repository) *Service { return &Service{Repo: r, Now: time.Now} }
func (s *Service) Notify(ctx context.Context, n *Models.Notification) error {
	if n == nil || n.UserID == 0 || len(strings.TrimSpace(n.Title)) == 0 || len(strings.TrimSpace(n.Body)) == 0 || len(n.Type) == 0 || len(n.Type) > 100 {
		return ErrInvalidNotification
	}
	n.Title = strings.TrimSpace(n.Title)
	n.Body = strings.TrimSpace(n.Body)
	if n.CreatedAt.IsZero() {
		n.CreatedAt = s.Now()
	}
	return s.Repo.Create(ctx, n)
}
func (s *Service) List(ctx context.Context, u uint64, limit int) ([]Models.Notification, error) {
	return s.Repo.List(ctx, u, limit)
}
func (s *Service) Read(ctx context.Context, u, id uint64) error {
	if u == 0 || id == 0 {
		return ErrInvalidNotification
	}
	return s.Repo.MarkRead(ctx, id, u, s.Now())
}
func (s *Service) ReadAll(ctx context.Context, u uint64) error {
	if u == 0 {
		return ErrInvalidNotification
	}
	return s.Repo.MarkAllRead(ctx, u, s.Now())
}
func (s *Service) Unread(ctx context.Context, u uint64) (int, error) {
	return s.Repo.UnreadCount(ctx, u)
}
func (s *Service) SetPreference(ctx context.Context, p *Models.Preference) error {
	if p == nil || p.UserID == 0 || p.EventType == "" || p.Channel == "" {
		return ErrInvalidNotification
	}
	p.UpdatedAt = s.Now()
	return s.Repo.SetPreference(ctx, p)
}
