package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Auth/Models"
	"github.com/alumasinde/jijenge/Core/Database"
)

type MySQLUserRepository struct {
	DB *Database.DB
}

func NewMySQLUserRepository(db *Database.DB) *MySQLUserRepository {
	return &MySQLUserRepository{DB: db}
}

func (r *MySQLUserRepository) Create(ctx context.Context, user *Models.User) error {
	res, err := r.DB.SQL.ExecContext(ctx, `
INSERT INTO users (public_id, email, password_hash, status)
VALUES (?, ?, ?, ?)`,
		user.PublicID, strings.ToLower(strings.TrimSpace(user.Email)), user.PasswordHash, user.Status)
	if err != nil {
		if strings.Contains(strings.ToLower(err.Error()), "duplicate") {
			return ErrEmailExists
		}
		return err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return err
	}
	user.ID = uint64(id)
	return nil
}

func (r *MySQLUserRepository) FindByEmail(ctx context.Context, email string) (*Models.User, error) {
	row := r.DB.SQL.QueryRowContext(ctx, `
SELECT id, public_id, email, password_hash, status, created_at, updated_at
FROM users
WHERE email = ?
LIMIT 1`, strings.ToLower(strings.TrimSpace(email)))
	var u Models.User
	if err := row.Scan(&u.ID, &u.PublicID, &u.Email, &u.PasswordHash, &u.Status, &u.CreatedAt, &u.UpdatedAt); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, ErrUserNotFound
		}
		return nil, err
	}
	return &u, nil
}

func (r *MySQLUserRepository) FindByID(ctx context.Context, id uint64) (*Models.User, error) {
	row := r.DB.SQL.QueryRowContext(ctx, `
SELECT id, public_id, email, password_hash, status, created_at, updated_at
FROM users
WHERE id = ?
LIMIT 1`, id)
	var u Models.User
	if err := row.Scan(&u.ID, &u.PublicID, &u.Email, &u.PasswordHash, &u.Status, &u.CreatedAt, &u.UpdatedAt); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, ErrUserNotFound
		}
		return nil, err
	}
	return &u, nil
}

var _ = time.Second
