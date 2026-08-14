package Repositories

import (
	"context"
	"github.com/alumasinde/jijenge/Auth/Models"
	"github.com/alumasinde/jijenge/Core/Security"
	"testing"
	"time"
)

func TestRotateRefreshIsAtomicInMemory(t *testing.T) {
	r := NewMemorySessionRepository()
	old := &Models.Session{UserID: 1, TokenHash: Security.HashToken("old-refresh"), ExpiresAt: time.Now().Add(time.Hour), CreatedAt: time.Now()}
	if e := r.Create(context.Background(), old); e != nil {
		t.Fatal(e)
	}
	next := &Models.Session{UserID: 1, TokenHash: Security.HashToken("new-refresh"), ExpiresAt: time.Now().Add(time.Hour), CreatedAt: time.Now()}
	if e := r.RotateRefresh(context.Background(), old.ID, next, time.Now()); e != nil {
		t.Fatal(e)
	}
	if _, e := r.FindActiveByTokenHash(context.Background(), old.TokenHash, time.Now()); e == nil {
		t.Fatal("old session still active")
	}
	if _, e := r.FindActiveByTokenHash(context.Background(), next.TokenHash, time.Now()); e != nil {
		t.Fatal("new session not active")
	}
}
