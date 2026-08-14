package Repositories

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Services/Models"
	"sync"
)

var (
	ErrNotFound  = errors.New("service not found")
	ErrDuplicate = errors.New("service already exists")
)

type Repository interface {
	CreateCategory(context.Context, *Models.Category) error
	Create(context.Context, *Models.Service) error
	Find(context.Context, uint64) (*Models.Service, error)
	ListByCategory(context.Context, uint64) []*Models.Service
}
type MemoryRepository struct {
	mu            sync.RWMutex
	next, catNext uint64
	items         map[uint64]*Models.Service
	cats          map[uint64]*Models.Category
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{next: 1, catNext: 1, items: map[uint64]*Models.Service{}, cats: map[uint64]*Models.Category{}}
}
func (r *MemoryRepository) CreateCategory(ctx context.Context, c *Models.Category) error {
	if e := ctx.Err(); e != nil {
		return e
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	c.ID = r.catNext
	r.catNext++
	r.cats[c.ID] = c
	return nil
}
func (r *MemoryRepository) Create(ctx context.Context, s *Models.Service) error {
	if e := ctx.Err(); e != nil {
		return e
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.cats[s.CategoryID]; !ok {
		return ErrNotFound
	}
	s.ID = r.next
	r.next++
	r.items[s.ID] = s
	return nil
}
func (r *MemoryRepository) Find(ctx context.Context, id uint64) (*Models.Service, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	s, ok := r.items[id]
	if !ok {
		return nil, ErrNotFound
	}
	x := *s
	return &x, nil
}
func (r *MemoryRepository) ListByCategory(ctx context.Context, id uint64) []*Models.Service {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := []*Models.Service{}
	for _, s := range r.items {
		if s.CategoryID == id && s.Status == Models.ServiceActive {
			x := *s
			out = append(out, &x)
		}
	}
	return out
}
