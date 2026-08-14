package Repositories

import (
	"context"
	"errors"
	"strings"
	"sync"

	"github.com/alumasinde/jijenge/Auth/Models"
)

var (
	ErrUserNotFound = errors.New("user not found")
	ErrEmailExists  = errors.New("email already exists")
)

type UserRepository interface {
	Create(ctx context.Context, user *Models.User) error
	FindByEmail(ctx context.Context, email string) (*Models.User, error)
	FindByID(ctx context.Context, id uint64) (*Models.User, error)
}

type MemoryUserRepository struct {
	mu      sync.RWMutex
	nextID  uint64
	byID    map[uint64]*Models.User
	byEmail map[string]uint64
}

func NewMemoryUserRepository() *MemoryUserRepository {
	return &MemoryUserRepository{
		nextID:  1,
		byID:    make(map[uint64]*Models.User),
		byEmail: make(map[string]uint64),
	}
}

func normalizeEmail(email string) string {
	return strings.ToLower(strings.TrimSpace(email))
}

func (r *MemoryUserRepository) Create(ctx context.Context, user *Models.User) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()

	email := normalizeEmail(user.Email)
	if _, exists := r.byEmail[email]; exists {
		return ErrEmailExists
	}

	copyUser := *user
	copyUser.ID = r.nextID
	r.nextID++
	copyUser.Email = email
	r.byID[copyUser.ID] = &copyUser
	r.byEmail[email] = copyUser.ID
	user.ID = copyUser.ID
	user.Email = copyUser.Email
	return nil
}

func (r *MemoryUserRepository) FindByEmail(ctx context.Context, email string) (*Models.User, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()

	id, ok := r.byEmail[normalizeEmail(email)]
	if !ok {
		return nil, ErrUserNotFound
	}
	user := *r.byID[id]
	return &user, nil
}

func (r *MemoryUserRepository) FindByID(ctx context.Context, id uint64) (*Models.User, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()

	user, ok := r.byID[id]
	if !ok {
		return nil, ErrUserNotFound
	}
	copyUser := *user
	return &copyUser, nil
}
