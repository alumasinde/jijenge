package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"github.com/alumasinde/jijenge/Audit/Models"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Core/Security"
	"time"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }
func (r *MySQLRepository) Record(ctx context.Context, e *Models.AuditEvent) error {
	if e == nil {
		return errors.New("nil audit event")
	}
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelSerializable}, func(tx *sql.Tx) error {
		var previous sql.NullString
		if err := tx.QueryRow(`SELECT event_hash FROM audit_events WHERE event_hash IS NOT NULL ORDER BY id DESC LIMIT 1 FOR UPDATE`).Scan(&previous); err != nil && !errors.Is(err, sql.ErrNoRows) {
			return err
		}
		if e.PublicID == "" {
			b, err := Security.GenerateToken(32)
			if err != nil {
				return err
			}
			e.PublicID = b[:26]
		}
		if previous.Valid {
			e.PreviousHash = previous.String
		} else {
			e.PreviousHash = ""
		}
		e.EventHash = Models.EventHash(e, e.PreviousHash)
		_, err := tx.Exec(`INSERT INTO audit_events(public_id,actor_user_id,action,resource_type,resource_id,request_id,ip_address,user_agent,outcome,reason,metadata,created_at,previous_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)`, e.PublicID, e.ActorUserID, e.Action, e.ResourceType, e.ResourceID, e.RequestID, e.IPAddress, e.UserAgent, e.Outcome, e.Reason, e.Metadata, e.CreatedAt, nullString(e.PreviousHash), e.EventHash)
		return err
	})
}
func (r *MySQLRepository) StartRun(ctx context.Context, x *Models.ReconciliationRun) error {
	if x.PublicID == "" {
		b, err := Security.GenerateToken(32)
		if err != nil {
			return err
		}
		x.PublicID = b[:26]
	}
	res, err := r.DB.SQL.ExecContext(ctx, `INSERT INTO reconciliation_runs(public_id,status,started_at) VALUES(?,?,?)`, x.PublicID, "running", x.StartedAt)
	if err != nil {
		return err
	}
	id, err := res.LastInsertId()
	x.ID = uint64(id)
	return err
}
func (r *MySQLRepository) AddIssue(ctx context.Context, x *Models.ReconciliationIssue) error {
	_, err := r.DB.SQL.ExecContext(ctx, `INSERT INTO reconciliation_issues(run_id,issue_type,account_id,transaction_id,expected_cents,actual_cents,details,created_at) VALUES(?,?,?,?,?,?,?,?)`, x.RunID, x.IssueType, x.AccountID, x.TransactionID, x.ExpectedCents, x.ActualCents, x.Details, x.CreatedAt)
	return err
}
func (r *MySQLRepository) FinishRun(ctx context.Context, id uint64, status string, a, t, d int64, at time.Time) error {
	res, err := r.DB.SQL.ExecContext(ctx, `UPDATE reconciliation_runs SET status=?,accounts_checked=?,transactions_checked=?,discrepancies=?,finished_at=? WHERE id=? AND status='running'`, status, a, t, d, at, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return errors.New("reconciliation run not found or already finished")
	}
	return nil
}
func _(_ *sql.DB) {}

func nullString(v string) any {
	if v == "" {
		return nil
	}
	return v
}

func (r *MySQLRepository) VerifyChain(ctx context.Context) error {
	rows, err := r.DB.SQL.QueryContext(ctx, `SELECT id,public_id,actor_user_id,action,resource_type,resource_id,request_id,ip_address,user_agent,outcome,reason,metadata,created_at,previous_hash,event_hash FROM audit_events WHERE event_hash IS NOT NULL ORDER BY id`)
	if err != nil {
		return err
	}
	defer rows.Close()
	var previous string
	for rows.Next() {
		var e Models.AuditEvent
		var actor sql.NullInt64
		var prev, hash sql.NullString
		if err := rows.Scan(&e.ID, &e.PublicID, &actor, &e.Action, &e.ResourceType, &e.ResourceID, &e.RequestID, &e.IPAddress, &e.UserAgent, &e.Outcome, &e.Reason, &e.Metadata, &e.CreatedAt, &prev, &hash); err != nil {
			return err
		}
		if actor.Valid {
			v := uint64(actor.Int64)
			e.ActorUserID = &v
		}
		if prev.Valid {
			e.PreviousHash = prev.String
		}
		e.EventHash = hash.String
		if e.PreviousHash != previous || e.EventHash != Models.EventHash(&e, e.PreviousHash) {
			return errors.New("audit chain integrity failure")
		}
		previous = e.EventHash
	}
	return rows.Err()
}
