package Database

import (
	"database/sql"
	"errors"
)

var ErrUnsupportedLockDialect = errors.New("unsupported database dialect")

// For MySQL, append FOR UPDATE to SELECT statements inside a transaction.
// This helper deliberately does not attempt to parse arbitrary SQL.
func ForUpdateMySQL(query string) string {
	return query + " FOR UPDATE"
}

func QueryRowForUpdate(tx *sql.Tx, query string, args ...any) *sql.Row {
	return tx.QueryRow(query+" FOR UPDATE", args...)
}
