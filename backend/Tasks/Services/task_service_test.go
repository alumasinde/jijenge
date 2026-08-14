package Services

import (
	"context"
	"github.com/alumasinde/jijenge/Tasks/Models"
	"github.com/alumasinde/jijenge/Tasks/Repositories"
	"testing"
)

func TestTaskLifecycleAndAuthorization(t *testing.T) {
	r := Repositories.NewMemoryRepository()
	s := New(r)
	ctx := context.Background()
	c := &Models.Category{Name: "Cleaning", Slug: "cleaning"}
	if err := r.CreateCategory(ctx, c); err != nil {
		t.Fatal(err)
	}
	task, err := s.CreateTask(ctx, 10, c.ID, "Clean office", "Deep clean", 5000, "KES")
	if err != nil {
		t.Fatal(err)
	}
	if err := s.PublishTask(ctx, 99, task.ID); err != Repositories.ErrForbidden {
		t.Fatalf("expected forbidden, got %v", err)
	}
	if err := s.PublishTask(ctx, 10, task.ID); err != nil {
		t.Fatal(err)
	}
	app, err := s.Apply(ctx, 20, task.ID, "I can do this", 4500)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.AcceptApplication(ctx, 20, app.ID); err != Repositories.ErrForbidden {
		t.Fatalf("expected forbidden, got %v", err)
	}
	asg, err := s.AcceptApplication(ctx, 10, app.ID)
	if err != nil {
		t.Fatal(err)
	}
	if err := s.Submit(ctx, 21, asg.ID); err != Repositories.ErrForbidden {
		t.Fatalf("expected forbidden, got %v", err)
	}
	if err := s.Submit(ctx, 20, asg.ID); err != nil {
		t.Fatal(err)
	}
	if err := s.Verify(ctx, 10, asg.ID); err != nil {
		t.Fatal(err)
	}
}
func TestInvalidTransitions(t *testing.T) {
	r := Repositories.NewMemoryRepository()
	s := New(r)
	ctx := context.Background()
	c := &Models.Category{Name: "X", Slug: "x"}
	_ = r.CreateCategory(ctx, c)
	task, _ := s.CreateTask(ctx, 1, c.ID, "X", "Y", 100, "KES")
	if err := s.CompleteTask(ctx, 1, task.ID); err != Repositories.ErrInvalidStateTransition {
		t.Fatalf("got %v", err)
	}
}
