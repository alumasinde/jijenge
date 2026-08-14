package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Core/Security"
	"github.com/alumasinde/jijenge/Financial/Models"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }

func (r *MySQLRepository) CreateAccount(ctx context.Context, a *Models.Account) error {
	if a == nil || a.Currency == "" || len(a.Currency) != 3 {
		return ErrCurrencyMismatch
	}
	if a.PublicID == "" {
		b, err := Security.GenerateToken(32)
		if err != nil {
			return err
		}
		a.PublicID = b[:26]
	}
	err := Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		res, err := tx.Exec(`INSERT INTO financial_accounts(public_id,owner_user_id,currency,status,created_at) VALUES(?,?,?,?,?)`, a.PublicID, a.OwnerUserID, strings.ToUpper(a.Currency), a.Status, a.CreatedAt)
		if err != nil {
			return err
		}
		id, err := res.LastInsertId()
		if err != nil {
			return err
		}
		a.ID = uint64(id)
		_, err = tx.Exec(`INSERT INTO financial_balances(account_id) VALUES(?)`, a.ID)
		return err
	})
	return err
}
func (r *MySQLRepository) GetAccount(ctx context.Context, id uint64) (*Models.Account, error) {
	var a Models.Account
	err := r.DB.SQL.QueryRowContext(ctx, `SELECT id,public_id,owner_user_id,currency,status,created_at FROM financial_accounts WHERE id=?`, id).
		Scan(&a.ID, &a.PublicID, &a.OwnerUserID, &a.Currency, &a.Status, &a.CreatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrAccountNotFound
	}
	if err != nil {
		return nil, err
	}
	return &a, nil
}
func (r *MySQLRepository) GetBalance(ctx context.Context, id uint64) (*Models.Balance, error) {
	var b Models.Balance
	err := r.DB.SQL.QueryRowContext(ctx, `SELECT b.account_id,a.currency,b.available_cents,b.held_cents FROM financial_balances b JOIN financial_accounts a ON a.id=b.account_id WHERE b.account_id=?`, id).Scan(&b.AccountID, &b.Currency, &b.AvailableCents, &b.HeldCents)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrAccountNotFound
	}
	if err != nil {
		return nil, err
	}
	return &b, nil
}
func (r *MySQLRepository) Transfer(ctx context.Context, key, publicID, desc string, from, to uint64, amount int64, now time.Time) (*Models.Transaction, error) {
	if amount <= 0 || from == to {
		return nil, ErrInvalidAmount
	}
	var out *Models.Transaction
	err := Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelSerializable}, func(tx *sql.Tx) error {
		var existingID uint64
		err := tx.QueryRow(`SELECT id FROM ledger_transactions WHERE idempotency_key=? FOR UPDATE`, key).Scan(&existingID)
		if err == nil {
			var cur, description string
			var created time.Time
			if e := tx.QueryRow(`SELECT currency,description,created_at FROM ledger_transactions WHERE id=?`, existingID).Scan(&cur, &description, &created); e != nil {
				return e
			}
			var d, c int64
			var af, at uint64
			rows, e := tx.Query(`SELECT account_id,debit_cents,credit_cents FROM ledger_entries WHERE transaction_id=? ORDER BY id`, existingID)
			if e != nil {
				return e
			}
			defer rows.Close()
			var entries []Models.Entry
			for rows.Next() {
				var x Models.Entry
				if e = rows.Scan(&x.AccountID, &x.DebitCents, &x.CreditCents); e != nil {
					return e
				}
				entries = append(entries, x)
			}
			if description != desc || len(entries) != 2 || entries[0].AccountID != from || entries[1].AccountID != to || entries[0].DebitCents != amount {
				return ErrIdempotencyConflict
			}
			_ = d
			_ = c
			_ = af
			_ = at
			out = &Models.Transaction{ID: existingID, IdempotencyKey: key, Currency: cur, Description: description, CreatedAt: created, Entries: entries}
			return nil
		}
		if !errors.Is(err, sql.ErrNoRows) {
			return err
		}
		// Always lock account rows in ascending ID order. This prevents the
		// classic A→B / B→A deadlock when concurrent transfers run in opposite
		// directions.
		first, second := from, to
		if first > second {
			first, second = second, first
		}
		type accountState struct {
			currency string
			status   Models.AccountStatus
		}
		states := make(map[uint64]accountState, 2)
		for _, id := range []uint64{first, second} {
			var st accountState
			if err = tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=? FOR UPDATE`, id).Scan(&st.currency, &st.status); errors.Is(err, sql.ErrNoRows) {
				return ErrAccountNotFound
			} else if err != nil {
				return err
			}
			states[id] = st
		}
		fc, fs := states[from].currency, states[from].status
		tc, ts := states[to].currency, states[to].status
		if fs != Models.AccountActive || ts != Models.AccountActive {
			return ErrAccountFrozen
		}
		if fc != tc {
			return ErrCurrencyMismatch
		}
		var fav, fh int64
		if err = tx.QueryRow(`SELECT available_cents,held_cents FROM financial_balances WHERE account_id=? FOR UPDATE`, from).Scan(&fav, &fh); err != nil {
			return err
		}
		if fav < amount {
			return ErrInsufficientFunds
		}
		if publicID == "" {
			b, e := Security.GenerateToken(32)
			if e != nil {
				return e
			}
			publicID = b[:26]
		}
		res, err := tx.Exec(`INSERT INTO ledger_transactions(public_id,idempotency_key,currency,description,created_at) VALUES(?,?,?,?,?)`, publicID, key, fc, desc, now)
		if err != nil {
			return err
		}
		id, err := res.LastInsertId()
		if err != nil {
			return err
		}
		if _, err = tx.Exec(`INSERT INTO ledger_entries(transaction_id,account_id,debit_cents) VALUES(?,?,?)`, id, from, amount); err != nil {
			return err
		}
		if _, err = tx.Exec(`INSERT INTO ledger_entries(transaction_id,account_id,credit_cents) VALUES(?,?,?)`, id, to, amount); err != nil {
			return err
		}
		if _, err = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents-? WHERE account_id=?`, amount, from); err != nil {
			return err
		}
		if _, err = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents+? WHERE account_id=?`, amount, to); err != nil {
			return err
		}
		out = &Models.Transaction{ID: uint64(id), PublicID: publicID, IdempotencyKey: key, Currency: fc, Description: desc, CreatedAt: now, Entries: []Models.Entry{{AccountID: from, DebitCents: amount}, {AccountID: to, CreditCents: amount}}}
		return nil
	})
	return out, err
}
func (r *MySQLRepository) CreateHold(ctx context.Context, key, reference string, account uint64, amount int64, now time.Time) (*Models.Hold, error) {
	if amount <= 0 {
		return nil, ErrInvalidAmount
	}
	var out *Models.Hold
	err := Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelSerializable}, func(tx *sql.Tx) error {
		var old Models.Hold
		e := tx.QueryRow(`SELECT id,public_id,account_id,reference,amount_cents,status,created_at,updated_at FROM ledger_holds WHERE reference=? FOR UPDATE`, reference).Scan(&old.ID, &old.PublicID, &old.AccountID, &old.Reference, &old.AmountCents, &old.Status, &old.CreatedAt, &old.UpdatedAt)
		if e == nil {
			if old.AccountID != account || old.AmountCents != amount {
				return ErrIdempotencyConflict
			}
			out = &old
			return nil
		}
		if !errors.Is(e, sql.ErrNoRows) {
			return e
		}
		var currency string
		var status Models.AccountStatus
		if e = tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=? FOR UPDATE`, account).Scan(&currency, &status); errors.Is(e, sql.ErrNoRows) {
			return ErrAccountNotFound
		} else if e != nil {
			return e
		}
		if status != Models.AccountActive {
			return ErrAccountFrozen
		}
		var available int64
		if e = tx.QueryRow(`SELECT available_cents FROM financial_balances WHERE account_id=? FOR UPDATE`, account).Scan(&available); e != nil {
			return e
		}
		if available < amount {
			return ErrInsufficientFunds
		}
		if key == "" {
			b, e := Security.GenerateToken(32)
			if e != nil {
				return e
			}
			key = b[:26]
		}
		res, e := tx.Exec(`INSERT INTO ledger_holds(public_id,account_id,reference,amount_cents,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)`, key, account, reference, amount, Models.HoldActive, now, now)
		if e != nil {
			return e
		}
		id, e := res.LastInsertId()
		if e != nil {
			return e
		}
		if _, e = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents-?,held_cents=held_cents+? WHERE account_id=?`, amount, amount, account); e != nil {
			return e
		}
		out = &Models.Hold{ID: uint64(id), PublicID: key, AccountID: account, Reference: reference, AmountCents: amount, Status: Models.HoldActive, CreatedAt: now, UpdatedAt: now}
		_ = currency
		return nil
	})
	return out, err
}
func (r *MySQLRepository) ReleaseHold(ctx context.Context, id uint64, now time.Time) error {
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelSerializable}, func(tx *sql.Tx) error {
		var account uint64
		var amount int64
		var status Models.HoldStatus
		e := tx.QueryRow(`SELECT account_id,amount_cents,status FROM ledger_holds WHERE id=? FOR UPDATE`, id).Scan(&account, &amount, &status)
		if errors.Is(e, sql.ErrNoRows) {
			return ErrHoldNotFound
		}
		if e != nil {
			return e
		}
		if status != Models.HoldActive {
			return ErrHoldState
		}
		if _, e = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents+?,held_cents=held_cents-? WHERE account_id=?`, amount, amount, account); e != nil {
			return e
		}
		_, e = tx.Exec(`UPDATE ledger_holds SET status=?,updated_at=? WHERE id=? AND status=?`, Models.HoldReleased, now, id, Models.HoldActive)
		return e
	})
}
func (r *MySQLRepository) CaptureHold(ctx context.Context, id, to uint64, amount int64, now time.Time) error {
	if amount <= 0 {
		return ErrInvalidAmount
	}
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelSerializable}, func(tx *sql.Tx) error {
		var from uint64
		var held int64
		var status Models.HoldStatus
		e := tx.QueryRow(`SELECT account_id,amount_cents,status FROM ledger_holds WHERE id=? FOR UPDATE`, id).Scan(&from, &held, &status)
		if errors.Is(e, sql.ErrNoRows) {
			return ErrHoldNotFound
		}
		if e != nil {
			return e
		}
		if status != Models.HoldActive || amount > held {
			return ErrHoldState
		}
		var fc, tc string
		var fs, ts Models.AccountStatus
		if e = tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=? FOR UPDATE`, from).Scan(&fc, &fs); errors.Is(e, sql.ErrNoRows) {
			return ErrAccountNotFound
		} else if e != nil {
			return e
		}
		if e = tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=? FOR UPDATE`, to).Scan(&tc, &ts); errors.Is(e, sql.ErrNoRows) {
			return ErrAccountNotFound
		} else if e != nil {
			return e
		}
		if fs != Models.AccountActive || ts != Models.AccountActive {
			return ErrAccountFrozen
		}
		if fc != tc {
			return ErrCurrencyMismatch
		}
		if _, e = tx.Exec(`UPDATE financial_balances SET held_cents=held_cents-? WHERE account_id=?`, amount, from); e != nil {
			return e
		}
		if _, e = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents+? WHERE account_id=?`, amount, to); e != nil {
			return e
		}
		newStatus := Models.HoldActive
		if amount == held {
			newStatus = Models.HoldCaptured
		}
		_, e = tx.Exec(`UPDATE ledger_holds SET amount_cents=CASE WHEN ?=? THEN amount_cents ELSE amount_cents-? END,status=?,updated_at=? WHERE id=?`, amount, held, amount, newStatus, now, id)
		return e
	})
}
var _ LedgerRepository = (*MySQLRepository)(nil)
