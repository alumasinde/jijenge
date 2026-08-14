package Repositories

import (
	"context"
	"github.com/alumasinde/jijenge/Admin/Models"
	"testing"
	"time"
)

func TestTwoPersonApproval(t *testing.T) {
	r := NewMemoryRepository()
	x := &Models.ActionRequest{Action: Models.BlockUser, TargetID: 8, RequestedBy: 2, Reason: "fraud review", CreatedAt: time.Now()}
	if e := r.CreateRequest(context.Background(), x); e != nil {
		t.Fatal(e)
	}
	if e := r.ApproveAndExecute(context.Background(), x.ID, 2, time.Now()); e != ErrSelfApproval {
		t.Fatal(e)
	}
	if e := r.ApproveAndExecute(context.Background(), x.ID, 3, time.Now()); e != nil {
		t.Fatal(e)
	}
	if r.userStatus[8] != "blocked" {
		t.Fatal("not blocked")
	}
}
func TestReject(t *testing.T) {
	r := NewMemoryRepository()
	x := &Models.ActionRequest{Action: Models.FreezeAccount, TargetID: 5, RequestedBy: 2, Reason: "risk review", CreatedAt: time.Now()}
	_ = r.CreateRequest(context.Background(), x)
	if e := r.Reject(context.Background(), x.ID, 3, time.Now()); e != nil {
		t.Fatal(e)
	}
	if r.items[x.ID].Status != "rejected" {
		t.Fatal("not rejected")
	}
}
