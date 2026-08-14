package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Settlements/Models"
	"strings"
	"time"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }
func (r *MySQLRepository) CreateForUser(ctx context.Context, x *Models.Settlement, user uint64) error {
	if user == 0 || x == nil || x.PayerUserID != user || x.Method == Models.Platform || strings.TrimSpace(x.EvidenceReference) == "" || len(x.EvidenceReference) > 255 || len(x.IdempotencyKey) < 16 || len(x.IdempotencyKey) > 128 {
		return ErrInvalidState
	}
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var existing Models.Settlement
		var claimed, confirmed sql.NullInt64
		var confirmedAt sql.NullTime
		err := tx.QueryRow(`SELECT id,public_id,task_id,assignment_id,payer_user_id,payee_user_id,method,amount_cents,currency,status,claimed_by,confirmed_by,confirmed_at,evidence_reference,confirmation_note,dispute_reason,idempotency_key,created_at,updated_at FROM settlements WHERE idempotency_key=? AND payer_user_id=?`, x.IdempotencyKey, user).Scan(&existing.ID, &existing.PublicID, &existing.TaskID, &existing.AssignmentID, &existing.PayerUserID, &existing.PayeeUserID, &existing.Method, &existing.AmountCents, &existing.Currency, &existing.Status, &claimed, &confirmed, &confirmedAt, &existing.EvidenceReference, &existing.ConfirmationNote, &existing.DisputeReason, &existing.IdempotencyKey, &existing.CreatedAt, &existing.UpdatedAt)
		if err == nil {
			if existing.TaskID != x.TaskID || existing.AssignmentID != x.AssignmentID || existing.PayeeUserID != x.PayeeUserID || existing.AmountCents != x.AmountCents || existing.Currency != x.Currency || existing.Method != x.Method {
				return ErrInvalidState
			}
			if claimed.Valid {
				v := uint64(claimed.Int64)
				existing.ClaimedBy = &v
			}
			if confirmed.Valid {
				v := uint64(confirmed.Int64)
				existing.ConfirmedBy = &v
			}
			if confirmedAt.Valid {
				existing.ConfirmedAt = &confirmedAt.Time
			}
			*x = existing
			return nil
		}
		if !errors.Is(err, sql.ErrNoRows) {
			return err
		}
		var taskID, owner, worker, taskAmount uint64
		var taskCurrency, taskStatus, assignmentStatus string
		if err := tx.QueryRow(`SELECT t.id,t.owner_user_id,t.budget_cents,t.currency,t.status,a.worker_user_id,a.status FROM tasks t JOIN task_assignments a ON a.task_id=t.id WHERE a.id=? FOR UPDATE`, x.AssignmentID).Scan(&taskID, &owner, &taskAmount, &taskCurrency, &taskStatus, &worker, &assignmentStatus); err != nil {
			return err
		}
		if taskID != x.TaskID || owner != user || worker != x.PayeeUserID || x.PayerUserID == x.PayeeUserID {
			return ErrInvalidState
		}
		if assignmentStatus != "submitted" && assignmentStatus != "verified" {
			return ErrInvalidState
		}
		var escrowID uint64
		if err := tx.QueryRow(`SELECT id FROM escrow_payments WHERE assignment_id=?`, x.AssignmentID).Scan(&escrowID); err == nil {
			return ErrInvalidState
		} else if !errors.Is(err, sql.ErrNoRows) {
			return err
		}
		if taskAmount != uint64(x.AmountCents) || taskCurrency != x.Currency {
			return ErrInvalidState
		}
		res, err := tx.Exec(`INSERT INTO settlements(public_id,task_id,assignment_id,payer_user_id,payee_user_id,method,amount_cents,currency,status,evidence_reference,idempotency_key,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)`, x.PublicID, x.TaskID, x.AssignmentID, x.PayerUserID, x.PayeeUserID, x.Method, x.AmountCents, x.Currency, Models.Pending, x.EvidenceReference, x.IdempotencyKey, x.CreatedAt, x.UpdatedAt)
		if err != nil {
			if strings.Contains(strings.ToLower(err.Error()), "duplicate") {
				return ErrDuplicate
			}
			return err
		}
		id, err := res.LastInsertId()
		if err != nil {
			return err
		}
		x.ID = uint64(id)
		x.Status = Models.Pending
		return nil
	})
}

func (r *MySQLRepository) Create(ctx context.Context, x *Models.Settlement) error {
	if x == nil || x.TaskID == 0 || x.AssignmentID == 0 || x.PayerUserID == 0 || x.PayeeUserID == 0 || x.AmountCents <= 0 || x.PayerUserID == x.PayeeUserID {
		return errors.New("invalid settlement")
	}
	res, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO settlements(public_id,task_id,assignment_id,payer_user_id,payee_user_id,method,amount_cents,currency,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)`, x.PublicID, x.TaskID, x.AssignmentID, x.PayerUserID, x.PayeeUserID, x.Method, x.AmountCents, x.Currency, Models.Pending, x.CreatedAt, x.UpdatedAt)
	if e != nil {
		if strings.Contains(strings.ToLower(e.Error()), "duplicate") {
			return ErrDuplicate
		}
		return e
	}
	id, e := res.LastInsertId()
	x.ID = uint64(id)
	x.Status = Models.Pending
	return e
}
func (r *MySQLRepository) Find(ctx context.Context, id uint64) (*Models.Settlement, error) {
	var x Models.Settlement
	var claimed, confirmed sql.NullInt64
	var confirmedAt sql.NullTime
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT id,public_id,task_id,assignment_id,payer_user_id,payee_user_id,method,amount_cents,currency,status,claimed_by,confirmed_by,confirmed_at,evidence_reference,confirmation_note,dispute_reason,idempotency_key,created_at,updated_at FROM settlements WHERE id=?`, id).Scan(&x.ID, &x.PublicID, &x.TaskID, &x.AssignmentID, &x.PayerUserID, &x.PayeeUserID, &x.Method, &x.AmountCents, &x.Currency, &x.Status, &claimed, &confirmed, &confirmedAt, &x.EvidenceReference, &x.ConfirmationNote, &x.DisputeReason, &x.IdempotencyKey, &x.CreatedAt, &x.UpdatedAt)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	if e != nil {
		return nil, e
	}
	if claimed.Valid {
		v := uint64(claimed.Int64)
		x.ClaimedBy = &v
	}
	if confirmed.Valid {
		v := uint64(confirmed.Int64)
		x.ConfirmedBy = &v
	}
	if confirmedAt.Valid {
		x.ConfirmedAt = &confirmedAt.Time
	}
	return &x, nil
}
func (r *MySQLRepository) Claim(ctx context.Context, id, user uint64, at time.Time) error {
	return r.resolve(ctx, id, `UPDATE settlements SET status='claimed',claimed_by=?,updated_at=? WHERE id=? AND status='pending' AND payer_user_id=?`, user, at, id, user)
}
func (r *MySQLRepository) Confirm(ctx context.Context, id, user uint64, at time.Time) error {
	return r.resolve(ctx, id, `UPDATE settlements SET status='confirmed',confirmed_by=?,confirmed_at=?,updated_at=? WHERE id=? AND status='claimed' AND payee_user_id=?`, user, at, at, id, user)
}
func (r *MySQLRepository) Dispute(ctx context.Context, id, user uint64, at time.Time) error {
	return r.resolve(ctx, id, `UPDATE settlements SET status='disputed',updated_at=? WHERE id=? AND status='claimed' AND (payer_user_id=? OR payee_user_id=?)`, at, id, user, user)
}
func (r *MySQLRepository) resolve(ctx context.Context, id uint64, q string, args ...any) error {
	res, e := r.DB.SQL.ExecContext(ctx, q, args...)
	if e != nil {
		return e
	}
	n, _ := res.RowsAffected()
	if n == 1 {
		return nil
	}
	var exists bool
	e = r.DB.SQL.QueryRowContext(ctx, `SELECT EXISTS(SELECT 1 FROM settlements WHERE id=?)`, id).Scan(&exists)
	if e != nil {
		return e
	}
	if !exists {
		return ErrNotFound
	}
	return ErrInvalidState
}

var _ Repository = (*MySQLRepository)(nil)

func (r *MySQLRepository) ConfirmWithNote(ctx context.Context, id, user uint64, note string, at time.Time) error {
	note = strings.TrimSpace(note)
	if note == "" || len(note) > 1000 {
		return ErrInvalidState
	}
	return r.resolve(ctx, id, `UPDATE settlements SET status='confirmed',confirmed_by=?,confirmed_at=?,confirmation_note=?,updated_at=? WHERE id=? AND status='claimed' AND payee_user_id=?`, user, at, note, at, id, user)
}
func (r *MySQLRepository) DisputeWithReason(ctx context.Context, id, user uint64, reason string, at time.Time) error {
	reason = strings.TrimSpace(reason)
	if len(reason) < 5 || len(reason) > 2000 {
		return ErrInvalidState
	}
	return r.resolve(ctx, id, `UPDATE settlements SET status='disputed',dispute_reason=?,updated_at=? WHERE id=? AND status='claimed' AND (payer_user_id=? OR payee_user_id=?)`, reason, at, id, user, user)
}
