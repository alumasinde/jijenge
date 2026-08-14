package Services

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"github.com/alumasinde/jijenge/Audit/Models"
	"github.com/alumasinde/jijenge/Audit/Repositories"
	"github.com/alumasinde/jijenge/Core/Database"
	"time"
)

type ReconciliationService struct {
	DB   *Database.DB
	Repo Repositories.Repository
	Now  func() time.Time
}

func NewReconciliationService(db *Database.DB, r Repositories.Repository) *ReconciliationService {
	return &ReconciliationService{DB: db, Repo: r, Now: time.Now}
}
func (s *ReconciliationService) Run(ctx context.Context) (*Models.ReconciliationRun, error) {
	run := &Models.ReconciliationRun{Status: "running", StartedAt: s.Now()}
	if err := s.Repo.StartRun(ctx, run); err != nil {
		return nil, err
	}
	var accounts, txns, issues int64
	err := Database.WithTx(ctx, s.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		if err := tx.QueryRowContext(ctx, `SELECT COUNT(*) FROM financial_accounts`).Scan(&accounts); err != nil {
			return err
		}
		if err := tx.QueryRowContext(ctx, `SELECT COUNT(*) FROM ledger_transactions`).Scan(&txns); err != nil {
			return err
		}
		rows, err := tx.QueryContext(ctx, `SELECT t.id,t.currency,COALESCE(SUM(e.debit_cents),0),COALESCE(SUM(e.credit_cents),0) FROM ledger_transactions t LEFT JOIN ledger_entries e ON e.transaction_id=t.id GROUP BY t.id,t.currency HAVING COALESCE(SUM(e.debit_cents),0)<>COALESCE(SUM(e.credit_cents),0)`)
		if err != nil {
			return err
		}
		defer rows.Close()
		for rows.Next() {
			var id uint64
			var cur string
			var debit, credit int64
			if err := rows.Scan(&id, &cur, &debit, &credit); err != nil {
				return err
			}
			issues++
			x := &Models.ReconciliationIssue{RunID: run.ID, IssueType: "unbalanced_ledger_transaction", TransactionID: &id, ExpectedCents: debit, ActualCents: credit, Details: fmt.Sprintf("currency=%s", cur), CreatedAt: s.Now()}
			if err := s.Repo.AddIssue(ctx, x); err != nil {
				return err
			}
		}
		if err := rows.Err(); err != nil {
			return err
		}
		// Detect balance rows with negative impossible values is unnecessary because UNSIGNED
		// enforces the invariant at the database layer. Detect held balances without active holds
		// is intentionally deferred until every hold-producing operation is represented by a
		// ledger transaction.
		return nil
	})
	status := "completed"
	if err != nil {
		status = "failed"
	}
	finishErr := s.Repo.FinishRun(ctx, run.ID, status, accounts, txns, issues, s.Now())
	if err != nil {
		return nil, err
	}
	if finishErr != nil {
		return nil, finishErr
	}
	if status == "failed" {
		return nil, errors.New("reconciliation failed")
	}
	run.Status = status
	run.AccountsChecked = accounts
	run.TransactionsChecked = txns
	run.Discrepancies = issues
	run.FinishedAt = ptr(s.Now())
	return run, nil
}
func ptr(t time.Time) *time.Time { return &t }
