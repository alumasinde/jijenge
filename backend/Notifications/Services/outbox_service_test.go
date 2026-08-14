package Services

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Notifications/Models"
	"github.com/alumasinde/jijenge/Notifications/Repositories"
	"testing"
	"time"
)

type testDelivery struct {
	fail bool
	seen []uint64
}

func (d *testDelivery) Deliver(ctx context.Context, o Models.Outbox) error {
	d.seen = append(d.seen, o.ID)
	if d.fail {
		return errors.New("provider unavailable")
	}
	return nil
}

func TestDispatcherMarksSuccessfulDelivery(t *testing.T) {
	r := Repositories.NewMemoryRepository()
	now := time.Now().UTC()
	n := &Models.Notification{UserID: 1, Channel: Models.Email, Title: "Hello", Body: "Body", Type: "test", CreatedAt: now}
	if err := r.Create(context.Background(), n); err != nil {
		t.Fatal(err)
	}
	d := NewDispatcher(r, &testDelivery{})
	d.Now = func() time.Time { return now }
	sent, err := d.Dispatch(context.Background(), 10)
	if err != nil || sent != 1 {
		t.Fatalf("sent=%d err=%v", sent, err)
	}
}
func TestDispatcherRetriesFailure(t *testing.T) {
	r := Repositories.NewMemoryRepository()
	now := time.Now().UTC()
	n := &Models.Notification{UserID: 1, Channel: Models.SMS, Title: "Hello", Body: "Body", Type: "test", CreatedAt: now}
	if err := r.Create(context.Background(), n); err != nil {
		t.Fatal(err)
	}
	d := NewDispatcher(r, &testDelivery{fail: true})
	d.Now = func() time.Time { return now }
	sent, err := d.Dispatch(context.Background(), 10)
	if err != nil || sent != 0 {
		t.Fatalf("sent=%d err=%v", sent, err)
	}
}
