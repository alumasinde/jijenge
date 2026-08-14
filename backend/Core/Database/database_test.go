package Database

import (
	"context"
	"database/sql"
	"testing"
	"time"
)

func TestOpenRequiresDSN(t *testing.T) {
	_, err := Open(context.Background(), "mysql", Config{})
	if err == nil {
		t.Fatal("expected missing DSN error")
	}
}

func TestTransactionRequiresDB(t *testing.T) {
	err := WithTx(context.Background(), nil, nil, func(*sql.Tx) error { return nil })
	if err == nil {
		t.Fatal("expected nil DB error")
	}
}

func TestForUpdateMySQL(t *testing.T) {
	got := ForUpdateMySQL("SELECT id FROM users WHERE id = ?")
	want := "SELECT id FROM users WHERE id = ? FOR UPDATE"
	if got != want {
		t.Fatalf("got %q, want %q", got, want)
	}
}

func TestDBCloseNil(t *testing.T) {
	var db *DB
	if err := db.Close(); err == nil {
		t.Fatal("expected nil DB error")
	}
	_ = time.Second
}
