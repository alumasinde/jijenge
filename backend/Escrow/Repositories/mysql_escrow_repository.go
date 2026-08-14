package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"

	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Core/Security"
	"github.com/alumasinde/jijenge/Escrow/Models"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }

func (r *MySQLRepository) CreateAndFundForUser(ctx context.Context, e *Models.Escrow, userID uint64) error {
	if userID == 0 || e == nil || len(e.IdempotencyKey) < 16 || len(e.IdempotencyKey) > 128 {
		return ErrInvalidResolution
	}
	return r.createAndFund(ctx, e, userID)
}

func (r *MySQLRepository) CreateAndFund(ctx context.Context, e *Models.Escrow) error {
	return r.createAndFund(ctx, e, 0)
}

func (r *MySQLRepository) createAndFund(ctx context.Context, e *Models.Escrow, requester uint64) error {
	if e.AmountCents <= 0 || e.PayerAccountID == 0 || e.WorkerAccountID == 0 {
		return errors.New("invalid escrow")
	}
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var existing Models.Escrow
		var rel sql.NullTime
		var fee uint64
		var dispute sql.NullInt64
		err := tx.QueryRow(`SELECT id,public_id,task_id,assignment_id,payer_account_id,worker_account_id,amount_cents,currency,status,created_at,updated_at,released_at,platform_fee_cents,dispute_id,idempotency_key FROM escrow_payments WHERE idempotency_key=? AND payer_account_id=?`, e.IdempotencyKey, e.PayerAccountID).Scan(&existing.ID, &existing.PublicID, &existing.TaskID, &existing.AssignmentID, &existing.PayerAccountID, &existing.WorkerAccountID, &existing.AmountCents, &existing.Currency, &existing.Status, &existing.CreatedAt, &existing.UpdatedAt, &rel, &fee, &dispute, &existing.IdempotencyKey)
		if err == nil {
			if existing.TaskID != e.TaskID || existing.AssignmentID != e.AssignmentID || existing.AmountCents != e.AmountCents || existing.Currency != e.Currency || existing.PayerAccountID != e.PayerAccountID || existing.WorkerAccountID != e.WorkerAccountID {
				return ErrInvalidResolution
			}
			*e = existing
			return nil
		}
		if !errors.Is(err, sql.ErrNoRows) {
			return err
		}
		var taskID, owner, worker uint64
		var taskStatus, assignStatus string
		var taskAmount uint64
		var taskCurrency, ownerCurrency, workerCurrency, ownerStatus, workerStatus string
		if err := Database.QueryRowForUpdate(tx, `SELECT t.id,t.owner_user_id,t.budget_cents,t.currency,t.status,a.worker_user_id,a.status FROM tasks t JOIN task_assignments a ON a.task_id=t.id WHERE a.id=?`, e.AssignmentID).Scan(&taskID, &owner, &taskAmount, &taskCurrency, &taskStatus, &worker, &assignStatus); err != nil {
			return err
		}
		if requester != 0 && owner != requester {
			return ErrInvalidResolution
		}
		if e.TaskID != taskID {
			return ErrInvalidResolution
		}
		if taskStatus != "in_progress" && taskStatus != "published" {
			return errors.New("task is not fundable")
		}
		if assignStatus != "assigned" {
			return errors.New("assignment is not fundable")
		}
		if taskAmount != uint64(e.AmountCents) || taskCurrency != e.Currency {
			return errors.New("escrow amount or currency mismatch")
		}
		if err := tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=? AND owner_user_id=?`, e.PayerAccountID, owner).Scan(&ownerCurrency, &ownerStatus); err != nil {
			return err
		}
		if err := tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=? AND owner_user_id=?`, e.WorkerAccountID, worker).Scan(&workerCurrency, &workerStatus); err != nil {
			return err
		}
		if ownerCurrency != e.Currency || workerCurrency != e.Currency || ownerStatus != "active" || workerStatus != "active" {
			return errors.New("escrow account mismatch")
		}
		var available uint64
		if err := Database.QueryRowForUpdate(tx, `SELECT available_cents FROM financial_balances WHERE account_id=?`, e.PayerAccountID).Scan(&available); err != nil {
			return err
		}
		if available < uint64(e.AmountCents) {
			return errors.New("insufficient funds")
		}
		var existingID uint64
		if err := tx.QueryRow(`SELECT id FROM escrow_payments WHERE assignment_id=?`, e.AssignmentID).Scan(&existingID); err == nil {
			return ErrEscrowExists
		} else if !errors.Is(err, sql.ErrNoRows) {
			return err
		}
		res, err := tx.Exec(`UPDATE financial_balances SET available_cents=available_cents-?,held_cents=held_cents+?,updated_at=? WHERE account_id=? AND available_cents>=?`, e.AmountCents, e.AmountCents, e.CreatedAt, e.PayerAccountID, e.AmountCents)
		if err != nil {
			return err
		}
		n, _ := res.RowsAffected()
		if n != 1 {
			return errors.New("balance changed during funding")
		}
		e.PublicID = publicID()
		e.PayerUserID = owner
		e.WorkerUserID = worker
		e.Status = Models.Funded
		res, err = tx.Exec(`INSERT INTO escrow_payments(public_id,task_id,assignment_id,payer_account_id,worker_account_id,amount_cents,currency,status,idempotency_key,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)`, e.PublicID, e.TaskID, e.AssignmentID, e.PayerAccountID, e.WorkerAccountID, e.AmountCents, e.Currency, e.Status, e.IdempotencyKey, e.CreatedAt, e.UpdatedAt)
		if err != nil {
			return err
		}
		id, err := res.LastInsertId()
		if err != nil {
			return err
		}
		e.ID = uint64(id)
		return nil
	})
}
func (r *MySQLRepository) Get(ctx context.Context, id uint64) (*Models.Escrow, error) {
	var e Models.Escrow
	var rel sql.NullTime
	var fee uint64
	var dispute sql.NullInt64
	err := r.DB.SQL.QueryRowContext(ctx, `SELECT id,public_id,task_id,assignment_id,payer_account_id,worker_account_id,amount_cents,currency,status,created_at,updated_at,released_at,platform_fee_cents,dispute_id FROM escrow_payments WHERE id=?`, id).Scan(&e.ID, &e.PublicID, &e.TaskID, &e.AssignmentID, &e.PayerAccountID, &e.WorkerAccountID, &e.AmountCents, &e.Currency, &e.Status, &e.CreatedAt, &e.UpdatedAt, &rel, &fee, &dispute)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrEscrowNotFound
	}
	if err != nil {
		return nil, err
	}
	if rel.Valid {
		e.ReleasedAt = &rel.Time
	}
	e.PlatformFeeCents = int64(fee)
	if dispute.Valid {
		x := uint64(dispute.Int64)
		e.DisputeID = &x
	}
	return &e, nil
}
func (r *MySQLRepository) GetByAssignment(ctx context.Context, assignmentID uint64) (*Models.Escrow, error) {
	var e Models.Escrow
	var rel sql.NullTime
	var fee uint64
	var dispute sql.NullInt64
	err := r.DB.SQL.QueryRowContext(ctx, `SELECT id,public_id,task_id,assignment_id,payer_account_id,worker_account_id,amount_cents,currency,status,created_at,updated_at,released_at,platform_fee_cents,dispute_id FROM escrow_payments WHERE assignment_id=?`, assignmentID).Scan(&e.ID, &e.PublicID, &e.TaskID, &e.AssignmentID, &e.PayerAccountID, &e.WorkerAccountID, &e.AmountCents, &e.Currency, &e.Status, &e.CreatedAt, &e.UpdatedAt, &rel, &fee, &dispute)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrEscrowNotFound
	}
	if err != nil {
		return nil, err
	}
	if rel.Valid {
		e.ReleasedAt = &rel.Time
	}
	e.PlatformFeeCents = int64(fee)
	if dispute.Valid {
		x := uint64(dispute.Int64)
		e.DisputeID = &x
	}
	return &e, nil
}

func (r *MySQLRepository) SubmitAssignment(ctx context.Context, assignmentID uint64, at time.Time) error {
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var status string
		if err := Database.QueryRowForUpdate(tx, `SELECT status FROM task_assignments WHERE id=?`, assignmentID).Scan(&status); err != nil {
			return err
		}
		if status != "submitted" {
			return ErrEscrowState
		}
		var escrowID uint64
		if err := tx.QueryRow(`SELECT id FROM escrow_payments WHERE assignment_id=?`, assignmentID).Scan(&escrowID); err != nil {
			return err
		}
		res, err := tx.Exec(`UPDATE escrow_payments SET status='submitted',updated_at=? WHERE id=? AND status='funded'`, at, escrowID)
		if err != nil {
			return err
		}
		if n, _ := res.RowsAffected(); n != 1 {
			return ErrEscrowState
		}
		return nil
	})
}

func (r *MySQLRepository) ReleaseVerifiedAssignmentForUser(ctx context.Context, assignmentID, userID uint64, at time.Time) error {
	if userID == 0 {
		return ErrInvalidResolution
	}
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var assignmentStatus, taskStatus string
		var owner uint64
		if err := Database.QueryRowForUpdate(tx, `SELECT t.owner_user_id,a.status,t.status FROM task_assignments a JOIN tasks t ON t.id=a.task_id WHERE a.id=?`, assignmentID).Scan(&owner, &assignmentStatus, &taskStatus); err != nil {
			return err
		}
		if owner != userID || assignmentStatus != "verified" {
			return ErrInvalidResolution
		}
		var escrowID uint64
		if err := tx.QueryRow(`SELECT id FROM escrow_payments WHERE assignment_id=?`, assignmentID).Scan(&escrowID); err != nil {
			return err
		}
		return r.settleInTx(tx, escrowID, 0, 0, at)
	})
}

func (r *MySQLRepository) ReleaseVerifiedAssignment(ctx context.Context, assignmentID uint64, at time.Time) error {
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var assignmentStatus string
		if err := Database.QueryRowForUpdate(tx, `SELECT status FROM task_assignments WHERE id=?`, assignmentID).Scan(&assignmentStatus); err != nil {
			return err
		}
		if assignmentStatus != "verified" {
			return ErrEscrowState
		}
		var escrowID uint64
		if err := tx.QueryRow(`SELECT id FROM escrow_payments WHERE assignment_id=?`, assignmentID).Scan(&escrowID); err != nil {
			return err
		}
		return r.settleInTx(tx, escrowID, 0, 0, at)
	})
}

func (r *MySQLRepository) MarkSubmitted(ctx context.Context, id uint64, at time.Time) error {
	res, err := r.DB.SQL.ExecContext(ctx, `UPDATE escrow_payments SET status='submitted',updated_at=? WHERE id=? AND status='funded'`, at, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return ErrEscrowState
	}
	return nil
}
func (r *MySQLRepository) OpenDispute(ctx context.Context, id, user uint64, reason string, at time.Time) (*Dispute, error) {
	if user == 0 || len(reason) == 0 || len(reason) > 2000 {
		return nil, ErrInvalidResolution
	}
	var d Dispute
	err := Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var status string
		var payerAccount, workerAccount uint64
		if err := Database.QueryRowForUpdate(tx, `SELECT status,payer_account_id,worker_account_id FROM escrow_payments WHERE id=?`, id).Scan(&status, &payerAccount, &workerAccount); err != nil {
			return err
		}
		if status != "submitted" && status != "verification_pending" {
			return ErrEscrowState
		}
		var payerUser, workerUser uint64
		if err := tx.QueryRow(`SELECT owner_user_id FROM financial_accounts WHERE id=?`, payerAccount).Scan(&payerUser); err != nil {
			return err
		}
		if err := tx.QueryRow(`SELECT owner_user_id FROM financial_accounts WHERE id=?`, workerAccount).Scan(&workerUser); err != nil {
			return err
		}
		if user != payerUser && user != workerUser {
			return ErrInvalidResolution
		}
		var exists uint64
		if err := tx.QueryRow(`SELECT id FROM escrow_disputes WHERE escrow_id=? AND status='open'`, id).Scan(&exists); err == nil {
			return ErrDisputeExists
		} else if !errors.Is(err, sql.ErrNoRows) {
			return err
		}
		d.PublicID = publicID()
		d.EscrowID = id
		d.OpenedByUserID = user
		d.Reason = reason
		d.Status = "open"
		d.CreatedAt = at
		res, err := tx.Exec(`INSERT INTO escrow_disputes(public_id,escrow_id,opened_by_user_id,reason,status,created_at) VALUES(?,?,?,?,?,?)`, d.PublicID, id, user, reason, "open", at)
		if err != nil {
			return err
		}
		x, _ := res.LastInsertId()
		d.ID = uint64(x)
		if _, err = tx.Exec(`UPDATE escrow_payments SET status='disputed',dispute_id=?,updated_at=? WHERE id=? AND status IN ('submitted','verification_pending')`, d.ID, at, id); err != nil {
			return err
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	return &d, nil
}
func (r *MySQLRepository) Refund(ctx context.Context, id uint64, at time.Time) error {
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var payer, amount uint64
		var status string
		if err := Database.QueryRowForUpdate(tx, `SELECT payer_account_id,amount_cents,status FROM escrow_payments WHERE id=?`, id).Scan(&payer, &amount, &status); err != nil {
			return err
		}
		if status == "refunded" {
			return nil
		}
		if status == "released" || status == "cancelled" {
			return ErrEscrowState
		}
		res, err := tx.Exec(`UPDATE financial_balances SET held_cents=held_cents-?,available_cents=available_cents+?,updated_at=? WHERE account_id=? AND held_cents>=?`, amount, amount, at, payer, amount)
		if err != nil {
			return err
		}
		n, _ := res.RowsAffected()
		if n != 1 {
			return errors.New("held balance changed")
		}
		res, err = tx.Exec(`UPDATE escrow_payments SET status='refunded',updated_at=? WHERE id=? AND status IN ('funded','submitted','verification_pending','disputed')`, at, id)
		if err != nil {
			return err
		}
		n, _ = res.RowsAffected()
		if n != 1 {
			return ErrEscrowState
		}
		return nil
	})
}
func (r *MySQLRepository) Release(ctx context.Context, id uint64, at time.Time) error {
	return r.ReleaseWithFee(ctx, id, 0, 0, at)
}
func (r *MySQLRepository) ReleaseWithFee(ctx context.Context, id uint64, fee int64, feeAccount uint64, at time.Time) error {
	if fee > 0 && feeAccount == 0 || fee < 0 {
		return ErrInvalidResolution
	}
	return r.settle(ctx, id, uint64(fee), feeAccount, 0, at)
}
func (r *MySQLRepository) settle(ctx context.Context, id uint64, fee uint64, feeAccount uint64, disputeID uint64, at time.Time) error {
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		return r.settleInTx(tx, id, fee, feeAccount, at)
	})
}

func (r *MySQLRepository) settleInTx(tx *sql.Tx, id uint64, fee uint64, feeAccount uint64, at time.Time) error {
	var payer, worker, amount uint64
	var currency, status string
	if err := Database.QueryRowForUpdate(tx, `SELECT payer_account_id,worker_account_id,amount_cents,currency,status FROM escrow_payments WHERE id=?`, id).Scan(&payer, &worker, &amount, &currency, &status); err != nil {
		return err
	}
	if status == "released" {
		return nil
	}
	if status != "submitted" && status != "verification_pending" {
		return ErrEscrowState
	}
	if fee > amount {
		return ErrInvalidResolution
	}
	workerNet := amount - fee
	first, second := payer, worker
	if fee > 0 && feeAccount != 0 && feeAccount < first {
		first = feeAccount
	}
	if worker < first {
		first = worker
	}
	accounts := []uint64{first}
	if second != first {
		second = payer
		if worker > second {
			second = worker
		}
		if fee > 0 && feeAccount > second {
			second = feeAccount
		}
		if second != first {
			accounts = append(accounts, second)
		}
	}
	var dummy uint64
	for _, a := range accounts {
		if err := Database.QueryRowForUpdate(tx, `SELECT account_id FROM financial_balances WHERE account_id=?`, a).Scan(&dummy); err != nil {
			return err
		}
	}
	var pc, ps, wc, ws string
	if err := tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=?`, payer).Scan(&pc, &ps); err != nil {
		return err
	}
	if err := tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=?`, worker).Scan(&wc, &ws); err != nil {
		return err
	}
	if pc != currency || wc != currency || ps != "active" || ws != "active" {
		return errors.New("settlement account invalid")
	}
	if fee > 0 {
		var fc, fs string
		if err := tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=?`, feeAccount).Scan(&fc, &fs); err != nil {
			return err
		}
		if fc != currency || fs != "active" {
			return errors.New("fee account invalid")
		}
	}
	res, err := tx.Exec(`UPDATE financial_balances SET held_cents=held_cents-?,updated_at=? WHERE account_id=? AND held_cents>=?`, amount, at, payer, amount)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return errors.New("held balance changed")
	}
	key := fmt.Sprintf("escrow-release:%d", id)
	var ledgerID uint64
	err = tx.QueryRow(`SELECT id FROM ledger_transactions WHERE idempotency_key=?`, key).Scan(&ledgerID)
	if errors.Is(err, sql.ErrNoRows) {
		res, err = tx.Exec(`INSERT INTO ledger_transactions(public_id,idempotency_key,currency,description,created_at) VALUES(?,?,?,?,?)`, publicID(), key, currency, "Jijenge escrow release", at)
		if err != nil {
			return err
		}
		x, _ := res.LastInsertId()
		ledgerID = uint64(x)
		if fee == 0 {
			_, err = tx.Exec(`INSERT INTO ledger_entries(transaction_id,account_id,debit_cents,credit_cents,created_at) VALUES(?,?,?,?,?),(?,?,?,?,?)`, ledgerID, payer, amount, 0, at, ledgerID, worker, 0, workerNet, at)
		} else {
			_, err = tx.Exec(`INSERT INTO ledger_entries(transaction_id,account_id,debit_cents,credit_cents,created_at) VALUES(?,?,?,?,?),(?,?,?,?,?),(?,?,?,?,?)`, ledgerID, payer, amount, 0, at, ledgerID, worker, 0, workerNet, at, ledgerID, feeAccount, 0, fee, at)
		}
		if err != nil {
			return err
		}
	} else if err != nil {
		return err
	}
	if _, err = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents+?,updated_at=? WHERE account_id=?`, workerNet, at, worker); err != nil {
		return err
	}
	if fee > 0 {
		if _, err = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents+?,updated_at=? WHERE account_id=?`, fee, at, feeAccount); err != nil {
			return err
		}
	}
	res, err = tx.Exec(`UPDATE escrow_payments SET status='released',released_at=?,platform_fee_cents=?,updated_at=? WHERE id=? AND status IN ('submitted','verification_pending')`, at, fee, at, id)
	if err != nil {
		return err
	}
	n, _ = res.RowsAffected()
	if n != 1 {
		return ErrEscrowState
	}
	return nil
}

func (r *MySQLRepository) ResolveDispute(ctx context.Context, disputeID uint64, resolution DisputeResolution, workerCents int64, feeAccount uint64, at time.Time) error {
	if disputeID == 0 || workerCents < 0 {
		return ErrInvalidResolution
	}
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var escrowID uint64
		var status string
		if err := Database.QueryRowForUpdate(tx, `SELECT escrow_id,status FROM escrow_disputes WHERE id=?`, disputeID).Scan(&escrowID, &status); err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				return ErrDisputeNotFound
			}
			return err
		}
		if status != "open" {
			return ErrResolutionExists
		}
		var amount uint64
		if err := Database.QueryRowForUpdate(tx, `SELECT amount_cents FROM escrow_payments WHERE id=? AND status='disputed'`, escrowID).Scan(&amount); err != nil {
			return err
		}
		switch resolution {
		case PayWorker:
			if workerCents != int64(amount) {
				return ErrInvalidResolution
			}
			if err := r.settleWithinTx(tx, escrowID, amount, 0, 0, at); err != nil {
				return err
			}
		case RefundPayer:
			if workerCents != 0 {
				return ErrInvalidResolution
			}
			if err := r.refundWithinTx(tx, escrowID, amount, at); err != nil {
				return err
			}
		case SplitSettlement:
			if workerCents <= 0 || workerCents >= int64(amount) || feeAccount == 0 {
				return ErrInvalidResolution
			}
			fee := uint64(int64(amount) - workerCents)
			if err := r.settleWithinTx(tx, escrowID, uint64(workerCents), fee, feeAccount, at); err != nil {
				return err
			}
		default:
			return ErrInvalidResolution
		}
		res, err := tx.Exec(`UPDATE escrow_disputes SET status='resolved',resolution=?,resolved_at=? WHERE id=? AND status='open'`, resolution, at, disputeID)
		if err != nil {
			return err
		}
		n, _ := res.RowsAffected()
		if n != 1 {
			return ErrResolutionExists
		}
		return nil
	})
}
func (r *MySQLRepository) settleWithinTx(tx *sql.Tx, id uint64, workerNet, fee, feeAccount uint64, at time.Time) error {
	var payer, worker, amount uint64
	var currency string
	if err := tx.QueryRow(`SELECT payer_account_id,worker_account_id,amount_cents,currency FROM escrow_payments WHERE id=? AND status='disputed'`).Scan(&payer, &worker, &amount, &currency); err != nil {
		return err
	}
	if workerNet+fee != amount {
		return ErrInvalidResolution
	}
	ids := []uint64{payer, worker}
	if fee > 0 {
		ids = append(ids, feeAccount)
	}
	// Lock in ascending order.
	for i := 0; i < len(ids); i++ {
		for j := i + 1; j < len(ids); j++ {
			if ids[j] < ids[i] {
				ids[i], ids[j] = ids[j], ids[i]
			}
		}
	}
	var dummy uint64
	for _, a := range ids {
		if err := Database.QueryRowForUpdate(tx, `SELECT account_id FROM financial_balances WHERE account_id=?`, a).Scan(&dummy); err != nil {
			return err
		}
	}
	res, err := tx.Exec(`UPDATE financial_balances SET held_cents=held_cents-?,updated_at=? WHERE account_id=? AND held_cents>=?`, amount, at, payer, amount)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return errors.New("held balance changed")
	}
	key := fmt.Sprintf("dispute-settlement:%d", id)
	var ledgerID uint64
	err = tx.QueryRow(`SELECT id FROM ledger_transactions WHERE idempotency_key=?`, key).Scan(&ledgerID)
	if errors.Is(err, sql.ErrNoRows) {
		res, err = tx.Exec(`INSERT INTO ledger_transactions(public_id,idempotency_key,currency,description,created_at) VALUES(?,?,?,?,?)`, publicID(), key, currency, "Jijenge dispute settlement", at)
		if err != nil {
			return err
		}
		x, _ := res.LastInsertId()
		ledgerID = uint64(x)
		if fee == 0 {
			_, err = tx.Exec(`INSERT INTO ledger_entries(transaction_id,account_id,debit_cents,credit_cents,created_at) VALUES(?,?,?,?,?),(?,?,?,?,?)`, ledgerID, payer, amount, 0, at, ledgerID, worker, 0, workerNet, at)
		} else {
			_, err = tx.Exec(`INSERT INTO ledger_entries(transaction_id,account_id,debit_cents,credit_cents,created_at) VALUES(?,?,?,?,?),(?,?,?,?,?),(?,?,?,?,?)`, ledgerID, payer, amount, 0, at, ledgerID, worker, 0, workerNet, at, ledgerID, feeAccount, 0, fee, at)
		}
		if err != nil {
			return err
		}
	} else if err != nil {
		return err
	}
	if _, err = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents+?,updated_at=? WHERE account_id=?`, workerNet, at, worker); err != nil {
		return err
	}
	if fee > 0 {
		if _, err = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents+?,updated_at=? WHERE account_id=?`, fee, at, feeAccount); err != nil {
			return err
		}
	}
	_, err = tx.Exec(`UPDATE escrow_payments SET status='released',released_at=?,platform_fee_cents=?,updated_at=? WHERE id=? AND status='disputed'`, at, fee, at, id)
	return err
}
func (r *MySQLRepository) refundWithinTx(tx *sql.Tx, id, amount uint64, at time.Time) error {
	var payer uint64
	if err := tx.QueryRow(`SELECT payer_account_id FROM escrow_payments WHERE id=? AND status='disputed'`, id).Scan(&payer); err != nil {
		return err
	}
	res, err := tx.Exec(`UPDATE financial_balances SET held_cents=held_cents-?,available_cents=available_cents+?,updated_at=? WHERE account_id=? AND held_cents>=?`, amount, amount, at, payer, amount)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return errors.New("held balance changed")
	}
	_, err = tx.Exec(`UPDATE escrow_payments SET status='refunded',updated_at=? WHERE id=? AND status='disputed'`, at, id)
	return err
}
func publicID() string {
	b, err := Security.GenerateToken(32)
	if err != nil {
		panic(err)
	}
	return b[:26]
}
