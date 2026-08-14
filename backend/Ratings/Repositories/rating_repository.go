package Repositories

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Ratings/Models"
	"sync"
)

var (
	ErrInvalid   = errors.New("invalid rating")
	ErrDuplicate = errors.New("rating already exists")
)

type Repository interface {
	Create(context.Context, *Models.Rating) error
	Average(context.Context, uint64) (float64, int, error)
}
type MemoryRepository struct {
	mu           sync.Mutex
	next         uint64
	items        map[uint64]*Models.Rating
	byAssignment map[uint64]bool
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{next: 1, items: map[uint64]*Models.Rating{}, byAssignment: map[uint64]bool{}}
}
func (r *MemoryRepository) Create(ctx context.Context, x *Models.Rating) error {
	if x == nil || x.AssignmentID == 0 || x.ReviewerUserID == 0 || x.RevieweeUserID == 0 || x.ReviewerUserID == x.RevieweeUserID || x.Score < 1 || x.Score > 5 {
		return ErrInvalid
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.byAssignment[x.AssignmentID] {
		return ErrDuplicate
	}
	x.ID = r.next
	r.next++
	r.byAssignment[x.AssignmentID] = true
	r.items[x.ID] = x
	return nil
}
func (r *MemoryRepository) Average(ctx context.Context, user uint64) (float64, int, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	var total int
	var n int
	for _, x := range r.items {
		if x.RevieweeUserID == user && x.Status == "published" {
			total += x.Score
			n++
		}
	}
	if n == 0 {
		return 0, 0, nil
	}
	return float64(total) / float64(n), n, nil
}
