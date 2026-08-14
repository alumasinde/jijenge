package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"github.com/alumasinde/jijenge/Admin/Models"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Core/Security"
	"time"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }
func (r *MySQLRepository) CreateRequest(ctx context.Context, x *Models.ActionRequest) error {
	if x == nil || x.TargetID == 0 || x.RequestedBy == 0 || x.Reason == "" || len(x.Reason) > 500 {
		return ErrInvalidAction
	}
	b, e := Security.GenerateToken(32)
	if e != nil {
		return e
	}
	x.PublicID = b[:26]
	x.Status = "pending"
	res, e := r.DB.SQL.ExecContext(ctx, `INSERT INTO admin_action_requests(public_id,action,target_id,requested_by,status,reason,created_at) VALUES(?,?,?,?,?,?,?)`, x.PublicID, x.Action, x.TargetID, x.RequestedBy, x.Status, x.Reason, x.CreatedAt)
	if e != nil {
		return e
	}
	id, e := res.LastInsertId()
	x.ID = uint64(id)
	return e
}
func (r *MySQLRepository) GetRequest(ctx context.Context, id uint64) (*Models.ActionRequest, error) {
	var x Models.ActionRequest
	var ap sql.NullInt64
	var at sql.NullTime
	e := r.DB.SQL.QueryRowContext(ctx, `SELECT id,public_id,action,target_id,requested_by,approved_by,status,reason,created_at,approved_at FROM admin_action_requests WHERE id=?`, id).Scan(&x.ID, &x.PublicID, &x.Action, &x.TargetID, &x.RequestedBy, &ap, &x.Status, &x.Reason, &x.CreatedAt, &at)
	if errors.Is(e, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	if e != nil {
		return nil, e
	}
	if ap.Valid {
		v := uint64(ap.Int64)
		x.ApprovedBy = &v
	}
	if at.Valid {
		x.ApprovedAt = &at.Time
	}
	return &x, nil
}
func (r *MySQLRepository) ApproveAndExecute(ctx context.Context, id, admin uint64, at time.Time) error {
	return r.resolve(ctx, id, admin, true, at)
}
func (r *MySQLRepository) Reject(ctx context.Context, id, admin uint64, at time.Time) error {
	return r.resolve(ctx, id, admin, false, at)
}
func (r *MySQLRepository) resolve(ctx context.Context, id, admin uint64, approve bool, at time.Time) error {
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var action string
		var target, requester uint64
		var status, reason string
		if e := Database.QueryRowForUpdate(tx, `SELECT action,target_id,requested_by,status,reason FROM admin_action_requests WHERE id=?`, id).Scan(&action, &target, &requester, &status, &reason); e != nil {
			if errors.Is(e, sql.ErrNoRows) {
				return ErrNotFound
			}
			return e
		}
		if status != "pending" {
			return ErrAlreadyResolved
		}
		if requester == admin {
			return ErrSelfApproval
		}
		if approve {
			switch Models.ActionType(action) {
			case Models.BlockUser, Models.UnblockUser:
				ns := "blocked"
				if action == string(Models.UnblockUser) {
					ns = "active"
				}
				if _, e := tx.Exec(`UPDATE users SET status=?,updated_at=? WHERE id=?`, ns, at, target); e != nil {
					return e
				}
			case Models.FreezeAccount, Models.UnfreezeAccount:
				ns := "frozen"
				if action == string(Models.UnfreezeAccount) {
					ns = "active"
				}
				if _, e := tx.Exec(`UPDATE financial_accounts SET status=? WHERE id=?`, ns, target); e != nil {
					return e
				}
			default:
				return ErrInvalidAction
			}
		}
		ns := "rejected"
		out := "denied"
		if approve {
			ns = "approved"
			out = "success"
		}
		res, e := tx.Exec(`UPDATE admin_action_requests SET status=?,approved_by=?,approved_at=? WHERE id=? AND status='pending'`, ns, admin, at, id)
		if e != nil {
			return e
		}
		n, _ := res.RowsAffected()
		if n != 1 {
			return ErrAlreadyResolved
		}
		b, e := Security.GenerateToken(32)
		if e != nil {
			return e
		}
		_, e = tx.Exec(`INSERT INTO audit_events(public_id,actor_user_id,action,resource_type,resource_id,outcome,reason,created_at) VALUES(?,?,?,?,?,?,?,?)`, b[:26], admin, "admin."+action, "admin_action", fmt.Sprint(id), out, reason, at)
		return e
	})
}
