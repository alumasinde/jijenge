package Repositories

import (
	"context"
	"errors"
	"fmt"
	"github.com/alumasinde/jijenge/Notifications/Models"
	"sync"
	"time"
)

var (
	ErrNotificationNotFound = errors.New("notification not found")
	ErrInvalidNotification  = errors.New("invalid notification")
	ErrPreferenceNotFound   = errors.New("notification preference not found")
	ErrInvalidPreference    = errors.New("invalid notification preference")
)

type Repository interface {
	Create(context.Context, *Models.Notification) error
	List(context.Context, uint64, int) ([]Models.Notification, error)
	MarkRead(context.Context, uint64, uint64, time.Time) error
	MarkAllRead(context.Context, uint64, time.Time) error
	UnreadCount(context.Context, uint64) (int, error)
	SetPreference(context.Context, *Models.Preference) error
	GetPreference(context.Context, uint64, Models.Channel, string) (bool, error)
	ClaimOutbox(context.Context, int, time.Time) ([]Models.Outbox, error)
	MarkOutboxSent(context.Context, uint64, time.Time) error
	MarkOutboxFailed(context.Context, uint64, string, time.Time) error
}

type MemoryRepository struct {
	mu         sync.Mutex
	next       uint64
	items      map[uint64]*Models.Notification
	prefs      map[string]Models.Preference
	outbox     map[uint64]*Models.Outbox
	nextOutbox uint64
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{next: 1, nextOutbox: 1, items: map[uint64]*Models.Notification{}, prefs: map[string]Models.Preference{}, outbox: map[uint64]*Models.Outbox{}}
}
func cp(n *Models.Notification) *Models.Notification  { x := *n; return &x }
func key(u uint64, c Models.Channel, e string) string { return fmt.Sprintf("%d|%s|%s", u, c, e) }
func (r *MemoryRepository) Create(ctx context.Context, n *Models.Notification) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if n == nil || n.UserID == 0 || n.Title == "" || n.Body == "" || n.Type == "" {
		return ErrInvalidNotification
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	n.ID = r.next
	r.next++
	n.Status = Models.Unread
	r.items[n.ID] = cp(n)
	if n.Channel != Models.InApp {
		if n.Channel != Models.Email && n.Channel != Models.SMS && n.Channel != Models.Push {
			delete(r.items, n.ID)
			return ErrInvalidNotification
		}
		o := &Models.Outbox{ID: r.nextOutbox, PublicID: fmt.Sprintf("outbox-%d", r.nextOutbox), NotificationID: n.ID, Channel: n.Channel, Status: Models.OutboxPending, AvailableAt: n.CreatedAt, CreatedAt: n.CreatedAt, UpdatedAt: n.CreatedAt}
		r.nextOutbox++
		r.outbox[o.ID] = o
	}
	return nil
}
func (r *MemoryRepository) List(ctx context.Context, u uint64, limit int) ([]Models.Notification, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if u == 0 {
		return nil, ErrInvalidNotification
	}
	if limit <= 0 || limit > 100 {
		limit = 50
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]Models.Notification, 0, limit)
	for i := r.next - 1; i > 0 && len(out) < limit; i-- {
		if n, ok := r.items[i]; ok && n.UserID == u {
			out = append(out, *cp(n))
		}
	}
	return out, nil
}
func (r *MemoryRepository) MarkRead(ctx context.Context, id, u uint64, at time.Time) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	n, ok := r.items[id]
	if !ok || n.UserID != u {
		return ErrNotificationNotFound
	}
	n.Status = Models.Read
	n.ReadAt = &at
	return nil
}
func (r *MemoryRepository) MarkAllRead(ctx context.Context, u uint64, at time.Time) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, n := range r.items {
		if n.UserID == u && n.Status == Models.Unread {
			n.Status = Models.Read
			n.ReadAt = &at
		}
	}
	return nil
}
func (r *MemoryRepository) UnreadCount(ctx context.Context, u uint64) (int, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	c := 0
	for _, n := range r.items {
		if n.UserID == u && n.Status == Models.Unread {
			c++
		}
	}
	return c, nil
}
func (r *MemoryRepository) SetPreference(ctx context.Context, p *Models.Preference) error {
	if p == nil || p.UserID == 0 || p.EventType == "" {
		return ErrInvalidPreference
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	p.UpdatedAt = time.Now()
	r.prefs[key(p.UserID, p.Channel, p.EventType)] = *p
	return nil
}
func (r *MemoryRepository) GetPreference(ctx context.Context, u uint64, c Models.Channel, e string) (bool, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.prefs[key(u, c, e)]
	if !ok {
		return true, nil
	}
	return p.Enabled, nil
}

func (r *MemoryRepository) ClaimOutbox(ctx context.Context, limit int, now time.Time) ([]Models.Outbox, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if limit <= 0 || limit > 100 {
		limit = 50
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]Models.Outbox, 0, limit)
	for _, o := range r.outbox {
		if len(out) >= limit {
			break
		}
		if (o.Status == Models.OutboxPending || o.Status == Models.OutboxFailed) && !o.AvailableAt.After(now) {
			o.Status = Models.OutboxProcessing
			o.Attempts++
			o.UpdatedAt = now
			o.LockedAt = &now
			out = append(out, *o)
		}
	}
	return out, nil
}
func (r *MemoryRepository) MarkOutboxSent(ctx context.Context, id uint64, now time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	o, ok := r.outbox[id]
	if !ok {
		return ErrNotificationNotFound
	}
	if o.Status != Models.OutboxProcessing {
		return ErrInvalidNotification
	}
	o.Status = Models.OutboxSent
	o.SentAt = &now
	o.UpdatedAt = now
	return nil
}
func (r *MemoryRepository) MarkOutboxFailed(ctx context.Context, id uint64, msg string, now time.Time) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if len(msg) > 1000 {
		return ErrInvalidNotification
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	o, ok := r.outbox[id]
	if !ok {
		return ErrNotificationNotFound
	}
	if o.Status != Models.OutboxProcessing {
		return ErrInvalidNotification
	}
	o.Status = Models.OutboxFailed
	o.LastError = msg
	o.UpdatedAt = now
	o.AvailableAt = now.Add(time.Second * time.Duration(minInt(o.Attempts*o.Attempts, 300)))
	return nil
}
func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}
