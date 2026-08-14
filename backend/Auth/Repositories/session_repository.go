package Repositories

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/alumasinde/jijenge/Auth/Models"
)

var ErrSessionNotFound = errors.New("session not found")

type SessionRepository interface {
	Create(ctx context.Context, session *Models.Session) error
	FindActiveByTokenHash(ctx context.Context, hash [32]byte, now time.Time) (*Models.Session, error)
	FindActiveByAccessTokenHash(ctx context.Context, hash [32]byte, now time.Time) (*Models.Session, error)
	Revoke(ctx context.Context, id uint64, at time.Time) error
	RevokeAllForUser(ctx context.Context, userID uint64, at time.Time) error
	Touch(ctx context.Context, id uint64, at time.Time) error
	RotateRefresh(ctx context.Context, oldID uint64, session *Models.Session, at time.Time) error
}

type MemorySessionRepository struct {
	mu       sync.RWMutex
	nextID   uint64
	sessions map[uint64]*Models.Session
}

func NewMemorySessionRepository() *MemorySessionRepository {
	return &MemorySessionRepository{nextID: 1, sessions: make(map[uint64]*Models.Session)}
}

func (r *MemorySessionRepository) Create(ctx context.Context, session *Models.Session) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	copySession := *session
	copySession.ID = r.nextID
	r.nextID++
	r.sessions[copySession.ID] = &copySession
	session.ID = copySession.ID
	return nil
}

func (r *MemorySessionRepository) FindActiveByTokenHash(ctx context.Context, hash [32]byte, now time.Time) (*Models.Session, error) {
	return r.find(ctx, func(s *Models.Session) bool { return s.TokenHash == hash }, now)
}

func (r *MemorySessionRepository) FindActiveByAccessTokenHash(ctx context.Context, hash [32]byte, now time.Time) (*Models.Session, error) {
	return r.find(ctx, func(s *Models.Session) bool { return s.AccessTokenHash == hash }, now)
}

func (r *MemorySessionRepository) find(ctx context.Context, match func(*Models.Session) bool, now time.Time) (*Models.Session, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	r.mu.RLock()
	defer r.mu.RUnlock()
	for _, session := range r.sessions {
		if match(session) && session.RevokedAt == nil && session.ExpiresAt.After(now) {
			copySession := *session
			return &copySession, nil
		}
	}
	return nil, ErrSessionNotFound
}

func (r *MemorySessionRepository) Revoke(ctx context.Context, id uint64, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	session, ok := r.sessions[id]
	if !ok {
		return ErrSessionNotFound
	}
	if session.RevokedAt == nil {
		t := at
		session.RevokedAt = &t
	}
	return nil
}

func (r *MemorySessionRepository) RevokeAllForUser(ctx context.Context, userID uint64, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, session := range r.sessions {
		if session.UserID == userID && session.RevokedAt == nil {
			t := at
			session.RevokedAt = &t
		}
	}
	return nil
}

func (r *MemorySessionRepository) Touch(ctx context.Context, id uint64, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	session, ok := r.sessions[id]
	if !ok {
		return ErrSessionNotFound
	}
	t := at
	session.LastSeenAt = &t
	return nil
}

func (r *MemorySessionRepository) RotateRefresh(ctx context.Context, oldID uint64, session *Models.Session, at time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if session == nil {
		return errors.New("session is nil")
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	old, ok := r.sessions[oldID]
	if !ok || old.RevokedAt != nil {
		return ErrSessionNotFound
	}
	t := at
	old.RevokedAt = &t
	copySession := *session
	copySession.ID = r.nextID
	r.nextID++
	r.sessions[copySession.ID] = &copySession
	session.ID = copySession.ID
	return nil
}
