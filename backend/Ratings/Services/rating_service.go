package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Ratings/Models"
	"github.com/alumasinde/jijenge/Ratings/Repositories"
	"strings"
	"time"
)

var ErrInvalid = errors.New("invalid rating")

type Service struct {
	Repo Repositories.Repository
	Now  func() time.Time
}

func New(r Repositories.Repository) *Service { return &Service{Repo: r, Now: time.Now} }
func (s *Service) Create(ctx context.Context, assignment, reviewer, reviewee uint64, score int, comment string) (*Models.Rating, error) {
	comment = strings.TrimSpace(comment)
	if assignment == 0 || reviewer == 0 || reviewee == 0 || reviewer == reviewee || score < 1 || score > 5 || len(comment) > 2000 {
		return nil, ErrInvalid
	}
	x := &Models.Rating{AssignmentID: assignment, ReviewerUserID: reviewer, RevieweeUserID: reviewee, Score: score, Comment: comment, Status: "published", CreatedAt: s.Now()}
	if e := s.Repo.Create(ctx, x); e != nil {
		return nil, e
	}
	return x, nil
}
