package Repositories

import (
	"context"
	"github.com/alumasinde/jijenge/Audit/Models"
	"testing"
	"time"
)

func TestMemoryAuditAndRun(t *testing.T) {
	r := NewMemoryRepository()
	now := time.Now()
	if err := r.Record(context.Background(), &Models.AuditEvent{Action: "task.verify", ResourceType: "task", CreatedAt: now}); err != nil {
		t.Fatal(err)
	}
	run := &Models.ReconciliationRun{Status: "running", StartedAt: now}
	if err := r.StartRun(context.Background(), run); err != nil {
		t.Fatal(err)
	}
	if err := r.FinishRun(context.Background(), run.ID, "completed", 2, 3, 1, now); err != nil {
		t.Fatal(err)
	}
	if r.Runs[run.ID].Discrepancies != 1 {
		t.Fatal("run not updated")
	}
}

func TestAuditChainDetectsTampering(t *testing.T) {
	r := NewMemoryRepository()
	now := time.Now().UTC()
	if err := r.Record(context.Background(), &Models.AuditEvent{PublicID: "evt-1", Action: "login", ResourceType: "session", Outcome: "success", CreatedAt: now}); err != nil {
		t.Fatal(err)
	}
	if err := r.Record(context.Background(), &Models.AuditEvent{PublicID: "evt-2", Action: "logout", ResourceType: "session", Outcome: "success", CreatedAt: now.Add(time.Second)}); err != nil {
		t.Fatal(err)
	}
	if err := r.VerifyChain(context.Background()); err != nil {
		t.Fatal(err)
	}
	r.Events[0].Action = "admin_delete"
	if err := r.VerifyChain(context.Background()); err == nil {
		t.Fatal("tampered audit chain was accepted")
	}
}
func TestAuditChainLinksEvents(t *testing.T) {
	r := NewMemoryRepository()
	now := time.Now().UTC()
	first := &Models.AuditEvent{PublicID: "evt-a", Action: "create", ResourceType: "task", Outcome: "success", CreatedAt: now}
	second := &Models.AuditEvent{PublicID: "evt-b", Action: "update", ResourceType: "task", Outcome: "success", CreatedAt: now.Add(time.Second)}
	if err := r.Record(context.Background(), first); err != nil {
		t.Fatal(err)
	}
	if err := r.Record(context.Background(), second); err != nil {
		t.Fatal(err)
	}
	if second.PreviousHash != first.EventHash {
		t.Fatal("audit events are not chained")
	}
	if len(first.EventHash) != 64 || len(second.EventHash) != 64 {
		t.Fatal("invalid SHA-256 audit hash")
	}
}
