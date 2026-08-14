package Repositories

import (
	"context"
	"github.com/alumasinde/jijenge/Notifications/Models"
	"testing"
	"time"
)

func TestNotificationLifecycle(t *testing.T) {
	r := NewMemoryRepository()
	n := &Models.Notification{UserID: 7, Channel: Models.InApp, Title: "Task assigned", Body: "A task was assigned", Type: "task.assigned", CreatedAt: time.Now()}
	if err := r.Create(context.Background(), n); err != nil {
		t.Fatal(err)
	}
	if c, _ := r.UnreadCount(context.Background(), 7); c != 1 {
		t.Fatalf("count=%d", c)
	}
	if err := r.MarkRead(context.Background(), n.ID, 7, time.Now()); err != nil {
		t.Fatal(err)
	}
	if c, _ := r.UnreadCount(context.Background(), 7); c != 0 {
		t.Fatalf("count=%d", c)
	}
}
func TestPreferenceDefaultEnabled(t *testing.T) {
	r := NewMemoryRepository()
	ok, err := r.GetPreference(context.Background(), 7, Models.Email, "task.assigned")
	if err != nil || !ok {
		t.Fatalf("default=%v err=%v", ok, err)
	}
}
