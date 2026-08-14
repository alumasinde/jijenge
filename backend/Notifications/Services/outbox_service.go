package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Notifications/Models"
	"github.com/alumasinde/jijenge/Notifications/Repositories"
	"strings"
	"time"
)

var ErrDelivery = errors.New("notification delivery failed")

type Delivery interface {
	Deliver(context.Context, Models.Outbox) error
}

type Dispatcher struct {
	Repo     Repositories.Repository
	Delivery Delivery
	Now      func() time.Time
}

func NewDispatcher(r Repositories.Repository, d Delivery) *Dispatcher {
	return &Dispatcher{Repo: r, Delivery: d, Now: time.Now}
}

// Dispatch claims a bounded batch. Each item is marked sent only after the
// provider confirms delivery. Failed items are retried with repository-controlled
// backoff. This is deliberately at-least-once: providers should use their own
// idempotency key (the outbox PublicID) when supported.
func (d *Dispatcher) Dispatch(ctx context.Context, limit int) (int, error) {
	if d == nil || d.Repo == nil || d.Delivery == nil {
		return 0, ErrDelivery
	}
	items, err := d.Repo.ClaimOutbox(ctx, limit, d.Now())
	if err != nil {
		return 0, err
	}
	sent := 0
	for _, item := range items {
		if err := d.Delivery.Deliver(ctx, item); err != nil {
			msg := strings.TrimSpace(err.Error())
			if msg == "" {
				msg = ErrDelivery.Error()
			}
			_ = d.Repo.MarkOutboxFailed(ctx, item.ID, msg, d.Now())
			continue
		}
		if err := d.Repo.MarkOutboxSent(ctx, item.ID, d.Now()); err != nil {
			return sent, err
		}
		sent++
	}
	return sent, nil
}
