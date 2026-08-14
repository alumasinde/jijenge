package integration

import (
	"context"
	"testing"
	"time"

	adminmodels "github.com/alumasinde/jijenge/Admin/Models"
	adminrepo "github.com/alumasinde/jijenge/Admin/Repositories"
	adminsvc "github.com/alumasinde/jijenge/Admin/Services"
	"github.com/alumasinde/jijenge/Auth/DTOs"
	authrepo "github.com/alumasinde/jijenge/Auth/Repositories"
	authsvc "github.com/alumasinde/jijenge/Auth/Services"
	escrowmodels "github.com/alumasinde/jijenge/Escrow/Models"
	escrowrepo "github.com/alumasinde/jijenge/Escrow/Repositories"
	escrowsvc "github.com/alumasinde/jijenge/Escrow/Services"
	finrepo "github.com/alumasinde/jijenge/Financial/Repositories"
	finsvc "github.com/alumasinde/jijenge/Financial/Services"
	notifmodels "github.com/alumasinde/jijenge/Notifications/Models"
	notifrepo "github.com/alumasinde/jijenge/Notifications/Repositories"
	notifsvc "github.com/alumasinde/jijenge/Notifications/Services"
	taskmodels "github.com/alumasinde/jijenge/Tasks/Models"
	taskrepo "github.com/alumasinde/jijenge/Tasks/Repositories"
	tasksvc "github.com/alumasinde/jijenge/Tasks/Services"
)

func TestPhase17CriticalFlow(t *testing.T) {
	ctx := context.Background()
	now := time.Now()

	// Authentication + refresh rotation.
	ur := authrepo.NewMemoryUserRepository()
	auth := authsvc.NewAuthService(ur, authrepo.NewMemorySessionRepository(), authsvc.Config{AccessTokenTTL: time.Minute, RefreshTokenTTL: time.Hour, MaxSessionLifetime: 24 * time.Hour})
	_, err := auth.Register(ctx, DTOs.RegisterRequest{Email: "owner@example.com", Password: "Owner123!Strong", FirstName: "Owner", LastName: "One"})
	if err != nil {
		t.Fatal(err)
	}
	login, err := auth.Login(ctx, DTOs.LoginRequest{Email: "owner@example.com", Password: "Owner123!Strong"})
	if err != nil {
		t.Fatal(err)
	}
	refreshed, err := auth.Refresh(ctx, login.RefreshToken)
	if err != nil || refreshed.RefreshToken == login.RefreshToken {
		t.Fatalf("refresh rotation failed: %v", err)
	}

	// Worker account.
	_, err = auth.Register(ctx, DTOs.RegisterRequest{Email: "worker@example.com", Password: "Worker123!Strong", FirstName: "Worker", LastName: "Two"})
	if err != nil {
		t.Fatal(err)
	}
	worker, _ := ur.FindByEmail(ctx, "worker@example.com")
	owner, _ := ur.FindByEmail(ctx, "owner@example.com")

	// Task lifecycle.
	tr := taskrepo.NewMemoryRepository()
	cat := &taskmodels.Category{Name: "Cleaning", Slug: "cleaning"}
	if err := tr.CreateCategory(ctx, cat); err != nil {
		t.Fatal(err)
	}
	ts := tasksvc.New(tr)
	ts.Now = func() time.Time { return now }
	task, err := ts.CreateTask(ctx, owner.ID, cat.ID, "Clean office", "Office cleaning", 100000, "KES")
	if err != nil {
		t.Fatal(err)
	}
	if err := ts.PublishTask(ctx, owner.ID, task.ID); err != nil {
		t.Fatal(err)
	}
	app, err := ts.Apply(ctx, worker.ID, task.ID, "I can do it", 100000)
	if err != nil {
		t.Fatal(err)
	}
	asg, err := ts.AcceptApplication(ctx, owner.ID, app.ID)
	if err != nil {
		t.Fatal(err)
	}
	if err := ts.Submit(ctx, worker.ID, asg.ID); err != nil {
		t.Fatal(err)
	}
	if err := ts.Verify(ctx, owner.ID, asg.ID); err != nil {
		t.Fatal(err)
	}

	// Ledger transfer + idempotent retry.
	lr := finrepo.NewMemoryRepository()
	ls := finsvc.New(lr)
	ls.Now = func() time.Time { return now }
	oa, err := ls.CreateAccount(ctx, &owner.ID, "KES")
	if err != nil {
		t.Fatal(err)
	}
	wa, err := ls.CreateAccount(ctx, &worker.ID, "KES")
	if err != nil {
		t.Fatal(err)
	}
	if err := lr.CreditForTest(oa.ID, 100000); err != nil {
		t.Fatal(err)
	}
	tx, err := ls.Transfer(ctx, "task-1", "task escrow", oa.ID, wa.ID, 50000)
	if err != nil {
		t.Fatal(err)
	}
	tx2, err := ls.Transfer(ctx, "task-1", "task escrow", oa.ID, wa.ID, 50000)
	if err != nil || tx2.ID != tx.ID {
		t.Fatalf("idempotency failed: %v", err)
	}

	// Escrow state machine.
	er := escrowrepo.NewMemoryRepository()
	es := escrowsvc.New(er)
	es.Now = func() time.Time { return now }
	e := &escrowmodels.Escrow{TaskID: task.ID, AssignmentID: asg.ID, PayerAccountID: oa.ID, WorkerAccountID: wa.ID, AmountCents: 50000, Currency: "KES"}
	if err := es.Fund(ctx, e); err != nil {
		t.Fatal(err)
	}
	if err := es.Submit(ctx, e.ID); err != nil {
		t.Fatal(err)
	}
	if err := es.VerifyAndReleaseWithFee(ctx, e.ID, 5000, 999); err != nil {
		t.Fatal(err)
	}
	got, err := er.Get(ctx, e.ID)
	if err != nil || got.Status != "released" || got.PlatformFeeCents != 5000 {
		t.Fatalf("escrow invalid: %+v %v", got, err)
	}

	// Notification lifecycle.
	nr := notifrepo.NewMemoryRepository()
	ns := notifsvc.New(nr)
	ns.Now = func() time.Time { return now }
	if err := ns.Notify(ctx, &notifmodels.Notification{UserID: worker.ID, Channel: notifmodels.InApp, Title: "Task verified", Body: "Your work was verified.", Type: "task.verified"}); err != nil {
		t.Fatal(err)
	}
	if c, _ := ns.Unread(ctx, worker.ID); c != 1 {
		t.Fatalf("unread=%d", c)
	}
	n, _ := ns.List(ctx, worker.ID, 20)
	if len(n) != 1 {
		t.Fatal("notification missing")
	}
	if err := ns.Read(ctx, worker.ID, n[0].ID); err != nil {
		t.Fatal(err)
	}

	// Two-person admin approval.
	ar := adminrepo.NewMemoryRepository()
	ads := adminsvc.New(ar)
	ads.Now = func() time.Time { return now }
	req, err := ads.Request(ctx, adminmodels.BlockUser, worker.ID, owner.ID, "fraud review")
	if err != nil {
		t.Fatal(err)
	}
	if err := ads.Approve(ctx, req.ID, owner.ID); err != adminrepo.ErrSelfApproval {
		t.Fatal("self approval allowed")
	}
	if err := ads.Approve(ctx, req.ID, 999); err != nil {
		t.Fatal(err)
	}
}

func TestPhase17InvariantGuards(t *testing.T) {
	ctx := context.Background()
	lr := finrepo.NewMemoryRepository()
	ls := finsvc.New(lr)
	a, _ := ls.CreateAccount(ctx, nil, "KES")
	b, _ := ls.CreateAccount(ctx, nil, "KES")
	if err := lr.CreditForTest(a.ID, 100); err != nil {
		t.Fatal(err)
	}
	if _, err := ls.Transfer(ctx, "x", "too much", a.ID, b.ID, 101); err == nil {
		t.Fatal("insufficient funds allowed")
	}
	if _, err := ls.Transfer(ctx, "x", "self", a.ID, a.ID, 1); err == nil {
		t.Fatal("self transfer allowed")
	}
}
