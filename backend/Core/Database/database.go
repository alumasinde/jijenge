package Database

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"
)

var (
	ErrNilDB = errors.New("database handle is nil")
)

type Config struct {
	DSN             string
	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
	ConnMaxIdleTime time.Duration
}

type DB struct {
	SQL *sql.DB
}

func Open(ctx context.Context, driver string, cfg Config) (*DB, error) {
	if cfg.DSN == "" {
		return nil, errors.New("database DSN is required")
	}
	if driver == "" {
		return nil, errors.New("database driver is required")
	}

	db, err := sql.Open(driver, cfg.DSN)
	if err != nil {
		return nil, fmt.Errorf("open database: %w", err)
	}

	if cfg.MaxOpenConns > 0 {
		db.SetMaxOpenConns(cfg.MaxOpenConns)
	}
	if cfg.MaxIdleConns > 0 {
		db.SetMaxIdleConns(cfg.MaxIdleConns)
	}
	if cfg.ConnMaxLifetime > 0 {
		db.SetConnMaxLifetime(cfg.ConnMaxLifetime)
	}
	if cfg.ConnMaxIdleTime > 0 {
		db.SetConnMaxIdleTime(cfg.ConnMaxIdleTime)
	}

	pingCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	if err := db.PingContext(pingCtx); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("ping database: %w", err)
	}

	return &DB{SQL: db}, nil
}

func (db *DB) Close() error {
	if db == nil || db.SQL == nil {
		return ErrNilDB
	}
	return db.SQL.Close()
}

func (db *DB) PingContext(ctx context.Context) error {
	if db == nil || db.SQL == nil {
		return ErrNilDB
	}
	return db.SQL.PingContext(ctx)
}

func (db *DB) BeginTx(ctx context.Context, opts *sql.TxOptions) (*sql.Tx, error) {
	if db == nil || db.SQL == nil {
		return nil, ErrNilDB
	}
	return db.SQL.BeginTx(ctx, opts)
}
