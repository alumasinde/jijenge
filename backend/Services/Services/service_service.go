package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Core/Security"
	"github.com/alumasinde/jijenge/Services/Models"
	"github.com/alumasinde/jijenge/Services/Repositories"
	"strings"
	"time"
)

var ErrInvalid = errors.New("invalid service")

type Service struct {
	Repo Repositories.Repository
	Now  func() time.Time
}

func New(r Repositories.Repository) *Service { return &Service{Repo: r, Now: time.Now} }
func (s *Service) Create(ctx context.Context, provider, category uint64, title, description, currency string, price int64) (*Models.Service, error) {
	title = strings.TrimSpace(title)
	currency = strings.ToUpper(strings.TrimSpace(currency))
	if provider == 0 || category == 0 || title == "" || len(title) > 200 || len(description) > 5000 || price < 0 || len(currency) != 3 {
		return nil, ErrInvalid
	}
	b, e := Security.GenerateToken(32)
	if e != nil {
		return nil, e
	}
	x := &Models.Service{PublicID: b[:26], ProviderUserID: provider, CategoryID: category, Title: title, Description: strings.TrimSpace(description), Currency: currency, StartingPriceCents: price, Status: Models.ServiceActive, CreatedAt: s.Now(), UpdatedAt: s.Now()}
	if e = s.Repo.Create(ctx, x); e != nil {
		return nil, e
	}
	return x, nil
}
