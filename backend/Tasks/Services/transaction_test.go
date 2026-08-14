package Services

import (
	"context"
	"github.com/alumasinde/jijenge/Tasks/Models"
	"github.com/alumasinde/jijenge/Tasks/Repositories"
	"sync"
	"testing"
)

func TestConcurrentAcceptOnlyOneAssignment(t *testing.T) {
	r := Repositories.NewMemoryRepository()
	s := New(r)
	ctx := context.Background()
	c := &Models.Category{Name: "Repair", Slug: "repair"}
	_ = r.CreateCategory(ctx, c)
	task, _ := s.CreateTask(ctx, 1, c.ID, "Repair", "Fix", 1000, "KES")
	_ = s.PublishTask(ctx, 1, task.ID)
	a1, _ := s.Apply(ctx, 2, task.ID, "me", 1000)
	a2, _ := s.Apply(ctx, 3, task.ID, "me too", 900)
	var wg sync.WaitGroup
	var mu sync.Mutex
	success := 0
	wg.Add(2)
	for _, id := range []uint64{a1.ID, a2.ID} {
		go func(id uint64) {
			defer wg.Done()
			if _, e := s.AcceptApplication(ctx, 1, id); e == nil {
				mu.Lock()
				success++
				mu.Unlock()
			}
		}(id)
	}
	wg.Wait()
	if success != 1 {
		t.Fatalf("expected one success, got %d", success)
	}
}
