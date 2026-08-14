//go:build mysqlintegration

package mysqlintegration

import (
	"context"
	"errors"
	"os"
	"strconv"
	"sync"
	"testing"
	"time"

	_ "github.com/go-sql-driver/mysql"

	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Financial/Models"
	FinancialRepos "github.com/alumasinde/jijenge/Financial/Repositories"
)

func openDB(t *testing.T) *Database.DB {
	t.Helper()
	dsn := os.Getenv("DB_DSN")
	if dsn == "" {
		t.Skip("DB_DSN is not set; run the Docker MySQL integration suite to execute this test")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	db, err := Database.Open(ctx, "mysql", Database.Config{
		DSN: dsn, MaxOpenConns: 30, MaxIdleConns: 10,
		ConnMaxLifetime: 10 * time.Minute, ConnMaxIdleTime: 2 * time.Minute,
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func newAccount(t *testing.T, repo *FinancialRepos.MySQLRepository) uint64 {
	t.Helper()
	a := &Models.Account{Currency: "KES", Status: Models.AccountActive, CreatedAt: time.Now()}
	if err := repo.CreateAccount(context.Background(), a); err != nil {
		t.Fatal(err)
	}
	return a.ID
}

func seed(t *testing.T, db *Database.DB, id uint64, cents int64) {
	t.Helper()
	if _, err := db.SQL.Exec(`UPDATE financial_balances SET available_cents=? WHERE account_id=?`, cents, id); err != nil {
		t.Fatal(err)
	}
}

func TestSchemaAndLedgerInvariants(t *testing.T) {
	db := openDB(t)
	var n int
	if err := db.SQL.QueryRow(`SELECT COUNT(*) FROM schema_migrations WHERE dirty=FALSE`).Scan(&n); err != nil {
		t.Fatal(err)
	}
	if n < 16 {
		t.Fatalf("expected at least 16 applied migrations, got %d", n)
	}

	repo := FinancialRepos.NewMySQLRepository(db)
	from := newAccount(t, repo)
	to := newAccount(t, repo)
	seed(t, db, from, 100_000)

	ctx := context.Background()
	tx, err := repo.Transfer(ctx, "integration-idem-1", "", "integration transfer", from, to, 10_000, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	retry, err := repo.Transfer(ctx, "integration-idem-1", "different-public-id", "integration transfer", from, to, 10_000, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	if retry.ID != tx.ID {
		t.Fatalf("idempotent retry created a different transaction: %d != %d", retry.ID, tx.ID)
	}

	_, err = repo.Transfer(ctx, "integration-idem-1", "", "wrong description", from, to, 10_000, time.Now())
	if !errors.Is(err, FinancialRepos.ErrIdempotencyConflict) {
		t.Fatalf("expected idempotency conflict, got %v", err)
	}

	b1, _ := repo.GetBalance(ctx, from)
	b2, _ := repo.GetBalance(ctx, to)
	if b1.AvailableCents != 90_000 || b2.AvailableCents != 10_000 {
		t.Fatalf("bad balances: from=%+v to=%+v", b1, b2)
	}
}

func TestConcurrentOppositeTransfersDoNotDeadlock(t *testing.T) {
	db := openDB(t)
	repo := FinancialRepos.NewMySQLRepository(db)
	a := newAccount(t, repo)
	b := newAccount(t, repo)
	seed(t, db, a, 100_000)
	seed(t, db, b, 100_000)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	const workers = 40
	var wg sync.WaitGroup
	errs := make(chan error, workers)
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			from, to := a, b
			if i%2 == 1 {
				from, to = b, a
			}
			_, err := repo.Transfer(ctx, fmtKey("opposite", i), "", "opposite", from, to, 1_000, time.Now())
			errs <- err
		}(i)
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	ba, _ := repo.GetBalance(ctx, a)
	bb, _ := repo.GetBalance(ctx, b)
	if ba.AvailableCents != 100_000 || bb.AvailableCents != 100_000 {
		t.Fatalf("balances changed unexpectedly: %+v %+v", ba, bb)
	}
}

func TestConcurrentSameIdempotencyKeyCreatesOneTransfer(t *testing.T) {
	db := openDB(t)
	repo := FinancialRepos.NewMySQLRepository(db)
	from := newAccount(t, repo)
	to := newAccount(t, repo)
	seed(t, db, from, 50_000)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	const workers = 20
	ids := make(chan uint64, workers)
	errs := make(chan error, workers)
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			x, e := repo.Transfer(ctx, key, "same-public", "same", from, to, 5_000, time.Now())
			if e != nil {
				errs <- e
				return
			}
			ids <- x.ID
		}()
	}
	wg.Wait()
	close(ids)
	close(errs)
	for e := range errs {
		t.Fatal(e)
	}
	var first uint64
	count := 0
	for id := range ids {
		if count == 0 {
			first = id
		} else if id != first {
			t.Fatalf("multiple transaction IDs: %d and %d", first, id)
		}
		count++
	}
	if count != workers {
		t.Fatalf("got %d successful idempotent results", count)
	}
	b, _ := repo.GetBalance(ctx, from)
	if b.AvailableCents != 45_000 {
		t.Fatalf("expected one debit, got %+v", b)
	}
	var ledgerCount int
	if err := db.SQL.QueryRow(`SELECT COUNT(*) FROM ledger_transactions WHERE idempotency_key=?`, "same-key").Scan(&ledgerCount); err != nil {
		t.Fatal(err)
	}
	if ledgerCount != 1 {
		t.Fatalf("expected one ledger transaction, got %d", ledgerCount)
	}
}

func TestHoldReferenceConflictAndAtomicRelease(t *testing.T) {
	db := openDB(t)
	repo := FinancialRepos.NewMySQLRepository(db)
	a := newAccount(t, repo)
	seed(t, db, a, 20_000)
	ctx := context.Background()
	h, err := repo.CreateHold(ctx, "hold-public", "unique-ref", a, 7_000, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	if _, err = repo.CreateHold(ctx, "other-public", "unique-ref", a, 6_000, time.Now()); !errors.Is(err, FinancialRepos.ErrIdempotencyConflict) {
		t.Fatalf("expected reference conflict, got %v", err)
	}
	b, _ := repo.GetBalance(ctx, a)
	if b.AvailableCents != 13_000 || b.HeldCents != 7_000 {
		t.Fatalf("bad held balance %+v", b)
	}
	if err = repo.ReleaseHold(ctx, h.ID, time.Now()); err != nil {
		t.Fatal(err)
	}
	b, _ = repo.GetBalance(ctx, a)
	if b.AvailableCents != 20_000 || b.HeldCents != 0 {
		t.Fatalf("release not atomic %+v", b)
	}
}

func fmtKey(prefix string, n int) string {
	return prefix + "-" + strconv.Itoa(n)
}
