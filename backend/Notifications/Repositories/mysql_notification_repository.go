package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Core/Security"
	"github.com/alumasinde/jijenge/Notifications/Models"
	"time"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }
func (r *MySQLRepository) Create(ctx context.Context, n *Models.Notification) error {
	if n == nil || n.UserID == 0 || n.Title == "" || n.Body == "" || n.Type == "" || len(n.Title) > 200 || len(n.Body) > 5000 {
		return ErrInvalidNotification
	}
	n.PublicID = publicID()
	n.Status = Models.Unread
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		res, err := tx.Exec(`INSERT INTO notifications(public_id,user_id,channel,title,body,event_type,reference_type,reference_id,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)`, n.PublicID, n.UserID, n.Channel, n.Title, n.Body, n.Type, n.ReferenceType, n.ReferenceID, n.Status, n.CreatedAt)
		if err != nil {
			return err
		}
		id, err := res.LastInsertId()
		if err != nil {
			return err
		}
		n.ID = uint64(id)
		if n.Channel != Models.InApp {
			if n.Channel != Models.Email && n.Channel != Models.SMS && n.Channel != Models.Push {
				return ErrInvalidNotification
			}
			outID := publicID()
			_, err = tx.Exec(`INSERT INTO notification_outbox(public_id,notification_id,channel,status,available_at,created_at,updated_at) VALUES(?,?,?,'pending',?,?,?)`, outID, n.ID, n.Channel, n.CreatedAt, n.CreatedAt, n.CreatedAt)
			if err != nil {
				return err
			}
		}
		return nil
	})
}
func (r *MySQLRepository) List(ctx context.Context, u uint64, limit int) ([]Models.Notification, error) {
	if limit <= 0 || limit > 100 {
		limit = 50
	}
	rows, err := r.DB.SQL.QueryContext(ctx, `SELECT id,public_id,user_id,channel,title,body,event_type,reference_type,reference_id,status,created_at,read_at FROM notifications WHERE user_id=? ORDER BY created_at DESC,id DESC LIMIT ?`, u, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []Models.Notification{}
	for rows.Next() {
		var n Models.Notification
		var rt, ri sql.NullString
		var ra sql.NullTime
		if err := rows.Scan(&n.ID, &n.PublicID, &n.UserID, &n.Channel, &n.Title, &n.Body, &n.Type, &rt, &ri, &n.Status, &n.CreatedAt, &ra); err != nil {
			return nil, err
		}
		if rt.Valid {
			n.ReferenceType = rt.String
		}
		if ri.Valid {
			n.ReferenceID = ri.String
		}
		if ra.Valid {
			n.ReadAt = &ra.Time
		}
		out = append(out, n)
	}
	return out, rows.Err()
}
func (r *MySQLRepository) MarkRead(ctx context.Context, id, u uint64, at time.Time) error {
	res, err := r.DB.SQL.ExecContext(ctx, `UPDATE notifications SET status='read',read_at=? WHERE id=? AND user_id=? AND status='unread'`, at, id, u)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return ErrNotificationNotFound
	}
	return nil
}
func (r *MySQLRepository) MarkAllRead(ctx context.Context, u uint64, at time.Time) error {
	_, err := r.DB.SQL.ExecContext(ctx, `UPDATE notifications SET status='read',read_at=? WHERE user_id=? AND status='unread'`, at, u)
	return err
}
func (r *MySQLRepository) UnreadCount(ctx context.Context, u uint64) (int, error) {
	var n int
	if err := r.DB.SQL.QueryRowContext(ctx, `SELECT COUNT(*) FROM notifications WHERE user_id=? AND status='unread'`, u).Scan(&n); err != nil {
		return 0, err
	}
	return n, nil
}
func (r *MySQLRepository) SetPreference(ctx context.Context, p *Models.Preference) error {
	if p == nil || p.UserID == 0 || p.EventType == "" {
		return ErrInvalidPreference
	}
	_, err := r.DB.SQL.ExecContext(ctx, `INSERT INTO notification_preferences(user_id,channel,event_type,enabled,updated_at) VALUES(?,?,?,?,?) ON DUPLICATE KEY UPDATE enabled=VALUES(enabled),updated_at=VALUES(updated_at)`, p.UserID, p.Channel, p.EventType, p.Enabled, p.UpdatedAt)
	return err
}
func (r *MySQLRepository) GetPreference(ctx context.Context, u uint64, c Models.Channel, e string) (bool, error) {
	var b bool
	err := r.DB.SQL.QueryRowContext(ctx, `SELECT enabled FROM notification_preferences WHERE user_id=? AND channel=? AND event_type=?`, u, c, e).Scan(&b)
	if errors.Is(err, sql.ErrNoRows) {
		return true, nil
	}
	return b, err
}
func publicID() string {
	b, err := Security.GenerateToken(32)
	if err != nil {
		panic(err)
	}
	return b[:26]
}

func (r *MySQLRepository) ClaimOutbox(ctx context.Context, limit int, now time.Time) ([]Models.Outbox, error) {
	if limit <= 0 || limit > 100 {
		limit = 50
	}
	var out []Models.Outbox
	err := Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		// Recover workers that died after claiming an item.
		_, err := tx.Exec(`UPDATE notification_outbox SET status='pending',locked_at=NULL,updated_at=? WHERE status='processing' AND locked_at IS NOT NULL AND locked_at < ?`, now, now.Add(-10*time.Minute))
		if err != nil {
			return err
		}
		rows, err := tx.Query(`SELECT id,public_id,notification_id,channel,status,attempts,available_at,locked_at,sent_at,last_error,created_at,updated_at FROM notification_outbox WHERE status IN ('pending','failed') AND available_at<=? ORDER BY id LIMIT ? FOR UPDATE SKIP LOCKED`, now, limit)
		if err != nil {
			return err
		}
		defer rows.Close()
		ids := make([]uint64, 0, limit)
		for rows.Next() {
			var o Models.Outbox
			var locked, sent sql.NullTime
			var last sql.NullString
			if err = rows.Scan(&o.ID, &o.PublicID, &o.NotificationID, &o.Channel, &o.Status, &o.Attempts, &o.AvailableAt, &locked, &sent, &last, &o.CreatedAt, &o.UpdatedAt); err != nil {
				return err
			}
			if locked.Valid {
				o.LockedAt = &locked.Time
			}
			if sent.Valid {
				o.SentAt = &sent.Time
			}
			if last.Valid {
				o.LastError = last.String
			}
			out = append(out, o)
			ids = append(ids, o.ID)
		}
		if err = rows.Err(); err != nil {
			return err
		}
		for _, id := range ids {
			if _, err = tx.Exec(`UPDATE notification_outbox SET status='processing',attempts=attempts+1,locked_at=?,updated_at=? WHERE id=?`, now, now, id); err != nil {
				return err
			}
		}
		for i := range out {
			out[i].Status = Models.OutboxProcessing
			out[i].Attempts++
			t := now
			out[i].LockedAt = &t
			out[i].UpdatedAt = now
		}
		return nil
	})
	return out, err
}
func (r *MySQLRepository) MarkOutboxSent(ctx context.Context, id uint64, now time.Time) error {
	res, err := r.DB.SQL.ExecContext(ctx, `UPDATE notification_outbox SET status='sent',sent_at=?,locked_at=NULL,updated_at=? WHERE id=? AND status='processing'`, now, now, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return ErrInvalidNotification
	}
	return nil
}
func (r *MySQLRepository) MarkOutboxFailed(ctx context.Context, id uint64, msg string, now time.Time) error {
	if len(msg) > 1000 {
		msg = msg[:1000]
	}
	res, err := r.DB.SQL.ExecContext(ctx, `UPDATE notification_outbox SET status='failed',last_error=?,locked_at=NULL,available_at=DATE_ADD(?,INTERVAL LEAST(300,POW(2,attempts)) SECOND),updated_at=? WHERE id=? AND status='processing'`, msg, now, now, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return ErrInvalidNotification
	}
	return nil
}
