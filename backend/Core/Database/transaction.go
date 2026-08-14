package Database

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
)

var ErrTransactionNil = errors.New("transaction is nil")

type TxFunc func(*sql.Tx) error

func WithTx(ctx context.Context, db *DB, opts *sql.TxOptions, fn TxFunc) (err error) {
	if db == nil || db.SQL == nil {
		return ErrNilDB
	}
	if fn == nil {
		return errors.New("transaction function is required")
	}

	tx, err := db.SQL.BeginTx(ctx, opts)
	if err != nil {
		return fmt.Errorf("begin transaction: %w", err)
	}

	defer func() {
		if recovered := recover(); recovered != nil {
			_ = tx.Rollback()
			panic(recovered)
		}

		if err != nil {
			if rollbackErr := tx.Rollback(); rollbackErr != nil && !errors.Is(rollbackErr, sql.ErrTxDone) {
				err = errors.Join(err, fmt.Errorf("rollback transaction: %w", rollbackErr))
			}
			return
		}

		if commitErr := tx.Commit(); commitErr != nil {
			err = fmt.Errorf("commit transaction: %w", commitErr)
		}
	}()

	if err = fn(tx); err != nil {
		return fmt.Errorf("transaction operation: %w", err)
	}

	return nil
}
