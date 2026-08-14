package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Providers/Models"
	"github.com/alumasinde/jijenge/Providers/Repositories"
	"strings"
	"time"
)

var ErrInvalid = errors.New("invalid provider data")

type Service struct {
	Repo Repositories.Repository
	Now  func() time.Time
}

func New(r Repositories.Repository) *Service { return &Service{Repo: r, Now: time.Now} }
func (s *Service) SaveProfile(ctx context.Context, p *Models.Profile) error {
	if p == nil || p.UserID == 0 || len(p.DisplayName) > 200 || p.ServiceRadiusKM < 0 || p.ServiceRadiusKM > 500 {
		return ErrInvalid
	}
	if p.CreatedAt.IsZero() {
		p.CreatedAt = s.Now()
	}
	p.UpdatedAt = s.Now()
	return s.Repo.UpsertProfile(ctx, p)
}
func (s *Service) SaveLocation(ctx context.Context, l *Models.Location) error {
	if l == nil || l.UserID == 0 || strings.TrimSpace(l.Country) == "" || l.Latitude < -90 || l.Latitude > 90 || l.Longitude < -180 || l.Longitude > 180 {
		return ErrInvalid
	}
	l.Country = strings.TrimSpace(l.Country)
	l.City = strings.TrimSpace(l.City)
	l.Area = strings.TrimSpace(l.Area)
	l.UpdatedAt = s.Now()
	return s.Repo.UpsertLocation(ctx, l)
}
