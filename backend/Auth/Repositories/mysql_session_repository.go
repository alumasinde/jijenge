package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"github.com/alumasinde/jijenge/Auth/Models"
	"github.com/alumasinde/jijenge/Core/Database"
)

type MySQLSessionRepository struct {
	DB *Database.DB
}

func NewMySQLSessionRepository(db *Database.DB) *MySQLSessionRepository {
	return &MySQLSessionRepository{DB: db}
}

func (r *MySQLSessionRepository) Create(ctx context.Context, session *Models.Session) error {
	res, err := r.DB.SQL.ExecContext(ctx, `
INSERT INTO sessions (user_id, token_hash, access_token_hash, expires_at, created_at, last_seen_at)
VALUES (?, ?, ?, ?, ?, ?)`,
		session.UserID, session.TokenHash[:], session.AccessTokenHash[:],
		session.ExpiresAt, session.CreatedAt, session.LastSeenAt)
	if err != nil {
		return err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return err
	}
	session.ID = uint64(id)
	return nil
}

func (r *MySQLSessionRepository) FindActiveByTokenHash(ctx context.Context, hash [32]byte, now time.Time) (*Models.Session, error) {
	return r.find(ctx, "token_hash", hash, now)
}

func (r *MySQLSessionRepository) FindActiveByAccessTokenHash(ctx context.Context, hash [32]byte, now time.Time) (*Models.Session, error) {
	return r.find(ctx, "access_token_hash", hash, now)
}

func (r *MySQLSessionRepository) find(ctx context.Context, column string, hash [32]byte, now time.Time) (*Models.Session, error) {
	query := `
SELECT id, user_id, access_token_hash, token_hash, expires_at, revoked_at, created_at, last_seen_at
FROM sessions
WHERE ` + column + ` = ?
  AND revoked_at IS NULL
  AND expires_at > ?
LIMIT 1`
	row := r.DB.SQL.QueryRowContext(ctx, query, hash[:], now)
	var s Models.Session
	var accessHash, refreshHash []byte
	if err := row.Scan(&s.ID, &s.UserID, &accessHash, &refreshHash, &s.ExpiresAt, &s.RevokedAt, &s.CreatedAt, &s.LastSeenAt); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, ErrSessionNotFound
		}
		return nil, err
	}
	if len(accessHash) == 32 {
		copy(s.AccessTokenHash[:], accessHash)
	}
	if len(refreshHash) == 32 {
		copy(s.TokenHash[:], refreshHash)
	}
	return &s, nil
}

func (r *MySQLSessionRepository) Revoke(ctx context.Context, id uint64, at time.Time) error {
	res, err := r.DB.SQL.ExecContext(ctx, `
UPDATE sessions
SET revoked_at = COALESCE(revoked_at, ?)
WHERE id = ?`, at, id)
	if err != nil {
		return err
	}
	n, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if n == 0 {
		return ErrSessionNotFound
	}
	return nil
}

func (r *MySQLSessionRepository) RevokeAllForUser(ctx context.Context, userID uint64, at time.Time) error {
	_, err := r.DB.SQL.ExecContext(ctx, `
UPDATE sessions
SET revoked_at = COALESCE(revoked_at, ?)
WHERE user_id = ? AND revoked_at IS NULL`, at, userID)
	return err
}

func (r *MySQLSessionRepository) Touch(ctx context.Context, id uint64, at time.Time) error {
	_, err := r.DB.SQL.ExecContext(ctx, `
UPDATE sessions SET last_seen_at = ? WHERE id = ?`, at, id)
	return err
}

func (r *MySQLSessionRepository) RotateRefresh(ctx context.Context, oldID uint64, session *Models.Session, at time.Time) error {
	if session == nil {
		return errors.New("session is nil")
	}
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		res, err := tx.ExecContext(ctx, `UPDATE sessions SET revoked_at=COALESCE(revoked_at, ?) WHERE id=? AND revoked_at IS NULL AND expires_at>?`, at, oldID, at)
		if err != nil {
			return err
		}
		n, err := res.RowsAffected()
		if err != nil || n != 1 {
			return ErrSessionNotFound
		}
		res, err = tx.ExecContext(ctx, `INSERT INTO sessions (user_id, token_hash, access_token_hash, expires_at, created_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?)`,
			session.UserID, session.TokenHash[:], session.AccessTokenHash[:], session.ExpiresAt, session.CreatedAt, session.LastSeenAt)
		if err != nil {
			return err
		}
		id, err := res.LastInsertId()
		if err != nil {
			return err
		}
		session.ID = uint64(id)
		return nil
	})
}
