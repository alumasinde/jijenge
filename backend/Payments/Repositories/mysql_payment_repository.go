package Repositories

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Payments/Models"
)

type MySQLRepository struct{ DB *Database.DB }

func NewMySQLRepository(db *Database.DB) *MySQLRepository { return &MySQLRepository{DB: db} }

func (r *MySQLRepository) CreatePayment(ctx context.Context, p *Models.Payment) error {
	_, err := r.DB.SQL.ExecContext(ctx, `INSERT INTO payments (public_id,provider,provider_ref,account_id,amount_cents,currency,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)`,
		p.PublicID, p.Provider, p.ProviderRef, p.AccountID, p.AmountCents, p.Currency, p.Status, p.CreatedAt, p.UpdatedAt)
	if err != nil && strings.Contains(strings.ToLower(err.Error()), "duplicate") {
		return ErrProviderRefExists
	}
	return err
}
func (r *MySQLRepository) GetPaymentByProviderRef(ctx context.Context, provider, ref string) (*Models.Payment, error) {
	var p Models.Payment
	err := r.DB.SQL.QueryRowContext(ctx, `SELECT id,public_id,provider,provider_ref,provider_event_id,account_id,amount_cents,currency,status,created_at,updated_at FROM payments WHERE provider=? AND provider_ref=?`, provider, ref).
		Scan(&p.ID, &p.PublicID, &p.Provider, &p.ProviderRef, &p.ProviderEventID, &p.AccountID, &p.AmountCents, &p.Currency, &p.Status, &p.CreatedAt, &p.UpdatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrPaymentNotFound
	}
	if err != nil {
		return nil, err
	}
	return &p, nil
}
func (r *MySQLRepository) RecordWebhook(ctx context.Context, e *Models.WebhookEvent) (bool, error) {
	res, err := r.DB.SQL.ExecContext(ctx, `INSERT INTO payment_webhook_events (provider,event_id,payment_ref,amount_cents,currency,signature,payload_hash,processed,created_at) VALUES (?,?,?,?,?,?,?,FALSE,?) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)`,
		e.Provider, e.EventID, e.PaymentRef, e.AmountCents, e.Currency, e.Signature, e.PayloadHash[:], e.CreatedAt)
	if err != nil {
		return false, err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return false, err
	}
	var processed bool
	err = r.DB.SQL.QueryRowContext(ctx, `SELECT processed FROM payment_webhook_events WHERE id=?`, id).Scan(&processed)
	if err != nil {
		return false, err
	}
	var stored [32]byte
	err = r.DB.SQL.QueryRowContext(ctx, `SELECT payload_hash FROM payment_webhook_events WHERE id=?`, id).Scan(&stored)
	if err != nil {
		return false, err
	}
	if stored != e.PayloadHash {
		return false, ErrWebhookConflict
	}
	e.ID = uint64(id)
	return processed, nil
}
func (r *MySQLRepository) MarkWebhookProcessed(ctx context.Context, id uint64, at time.Time) error {
	res, err := r.DB.SQL.ExecContext(ctx, `UPDATE payment_webhook_events SET processed=TRUE,processed_at=? WHERE id=? AND processed=FALSE`, at, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		var ok bool
		err = r.DB.SQL.QueryRowContext(ctx, `SELECT processed FROM payment_webhook_events WHERE id=?`, id).Scan(&ok)
		if err == nil && ok {
			return nil
		}
		return err
	}
	return nil
}
func (r *MySQLRepository) ConfirmPayment(ctx context.Context, id uint64, providerRef, eventID string, at time.Time) error {
	res, err := r.DB.SQL.ExecContext(ctx, `UPDATE payments SET status='confirmed',provider_ref=?,provider_event_id=?,updated_at=? WHERE id=? AND status='pending'`, providerRef, eventID, at, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 1 {
		return nil
	}
	var status string
	err = r.DB.SQL.QueryRowContext(ctx, `SELECT status FROM payments WHERE id=?`, id).Scan(&status)
	if errors.Is(err, sql.ErrNoRows) {
		return ErrPaymentNotFound
	}
	if err != nil {
		return err
	}
	if status == "confirmed" {
		return nil
	}
	return ErrPaymentState
}
func (r *MySQLRepository) FailPayment(ctx context.Context, id uint64, reason string, at time.Time) error {
	res, err := r.DB.SQL.ExecContext(ctx, `UPDATE payments SET status='failed',updated_at=? WHERE id=? AND status='pending'`, at, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 1 {
		return nil
	}
	return ErrPaymentState
}

// SettleConfirmedPayment atomically converts a confirmed provider payment into
// a double-entry ledger transfer from the provider clearing account to the
// user's financial account. Both the payment settlement marker and ledger
// mutation commit or roll back together.
func (r *MySQLRepository) SettleConfirmedPayment(ctx context.Context, paymentID, clearingAccountID uint64, idem string, at time.Time) error {
	if clearingAccountID == 0 || idem == "" {
		return ErrPaymentState
	}
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var provider, ref, event, currency, status string
		var account, amount uint64
		err := Database.QueryRowForUpdate(tx, `SELECT provider,provider_ref,provider_event_id,account_id,amount_cents,currency,status FROM payments WHERE id=?`, paymentID).
			Scan(&provider, &ref, &event, &account, &amount, &currency, &status)
		if errors.Is(err, sql.ErrNoRows) {
			return ErrPaymentNotFound
		}
		if err != nil {
			return err
		}
		if status != "confirmed" {
			return ErrPaymentState
		}

		var settled bool
		err = tx.QueryRow(`SELECT EXISTS(SELECT 1 FROM payment_settlements WHERE payment_id=?)`).Scan(&settled)
		if err != nil {
			return err
		}
		if settled {
			return nil
		}

		// Lock both balances in deterministic account order to avoid deadlocks.
		first, second := clearingAccountID, account
		if first > second {
			first, second = second, first
		}
		var dummy uint64
		if err = Database.QueryRowForUpdate(tx, `SELECT account_id FROM financial_balances WHERE account_id=?`, first).Scan(&dummy); err != nil {
			return err
		}
		if second != first {
			if err = Database.QueryRowForUpdate(tx, `SELECT account_id FROM financial_balances WHERE account_id=?`, second).Scan(&dummy); err != nil {
				return err
			}
		}

		var sourceCurrency, destCurrency, sourceStatus, destStatus string
		err = tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=?`, clearingAccountID).Scan(&sourceCurrency, &sourceStatus)
		if err != nil {
			return err
		}
		err = tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=?`, account).Scan(&destCurrency, &destStatus)
		if err != nil {
			return err
		}
		if sourceCurrency != currency || destCurrency != currency {
			return errors.New("settlement currency mismatch")
		}
		if sourceStatus != "active" || destStatus != "active" {
			return errors.New("settlement account inactive")
		}

		var available uint64
		if err = tx.QueryRow(`SELECT available_cents FROM financial_balances WHERE account_id=? FOR UPDATE`, clearingAccountID).Scan(&available); err != nil {
			return err
		}
		if available < amount {
			return errors.New("provider clearing balance insufficient")
		}

		// Create the immutable ledger transaction.
		var txID uint64
		createdLedger := false
		err = tx.QueryRow(`SELECT id FROM ledger_transactions WHERE idempotency_key=?`, idem).Scan(&txID)
		if err == nil {
			// Existing transaction is acceptable only if it is the settlement we expect.
			var cnt int
			if e := tx.QueryRow(`SELECT COUNT(*) FROM ledger_entries WHERE transaction_id=? AND ((account_id=? AND debit_cents=?) OR (account_id=? AND credit_cents=?))`, txID, clearingAccountID, amount, account, amount).Scan(&cnt); e != nil {
				return e
			}
			if cnt < 2 {
				return errors.New("idempotency key points to incompatible ledger transaction")
			}
		} else if errors.Is(err, sql.ErrNoRows) {
			res, e := tx.Exec(`INSERT INTO ledger_transactions (public_id,idempotency_key,currency,description,created_at) VALUES (?,?,?,?,?)`,
				newID(), idem, currency, fmt.Sprintf("PSP settlement %s:%s", provider, ref), at)
			if e != nil {
				return e
			}
			txID64, e := res.LastInsertId()
			if e != nil {
				return e
			}
			txID = uint64(txID64)
			createdLedger = true
			if _, e = tx.Exec(`INSERT INTO ledger_entries (transaction_id,account_id,debit_cents,credit_cents,created_at) VALUES (?,?,?,?,?),(?,?,?,?,?)`,
				txID, clearingAccountID, amount, 0, at, txID, account, 0, amount, at); e != nil {
				return e
			}
		} else {
			return err
		}

		if createdLedger {
			res, err := tx.Exec(`UPDATE financial_balances SET available_cents=available_cents-?,updated_at=? WHERE account_id=? AND available_cents>=?`, amount, at, clearingAccountID, amount)
			if err != nil {
				return err
			}
			if n, _ := res.RowsAffected(); n != 1 {
				return errors.New("provider clearing balance changed")
			}
			if _, err = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents+?,updated_at=? WHERE account_id=?`, amount, at, account); err != nil {
				return err
			}
		}

		_, err = tx.Exec(`INSERT INTO payment_settlements (payment_id,ledger_transaction_id,idempotency_key,amount_cents,currency,created_at) VALUES (?,?,?,?,?,?)`,
			paymentID, txID, idem, amount, currency, at)
		if err != nil {
			if strings.Contains(strings.ToLower(err.Error()), "duplicate") {
				return nil
			}
			return err
		}
		_, err = tx.Exec(`UPDATE payments SET updated_at=? WHERE id=?`, at, paymentID)
		return err
	})
}

func (r *MySQLRepository) ConfirmAndSettlePayment(ctx context.Context, paymentID uint64, providerRef, eventID string, clearingAccountID uint64, idem string, at time.Time) error {
	if clearingAccountID == 0 || idem == "" {
		return ErrPaymentState
	}
	return Database.WithTx(ctx, r.DB, &sql.TxOptions{Isolation: sql.LevelReadCommitted}, func(tx *sql.Tx) error {
		var provider, ref, oldEvent, currency, status string
		var account, amount uint64
		err := Database.QueryRowForUpdate(tx, `SELECT provider,provider_ref,provider_event_id,account_id,amount_cents,currency,status FROM payments WHERE id=?`, paymentID).
			Scan(&provider, &ref, &oldEvent, &account, &amount, &currency, &status)
		if errors.Is(err, sql.ErrNoRows) {
			return ErrPaymentNotFound
		}
		if err != nil {
			return err
		}
		if status == "confirmed" {
			// A second webhook may retry the same event, but a different event
			// must never be allowed to mutate/settle an already-confirmed payment.
			if ref != "" && ref != providerRef {
				return ErrProviderEventConflict
			}
			if oldEvent != "" && oldEvent != eventID {
				return ErrWebhookConflict
			}
			var settled bool
			if e := tx.QueryRow(`SELECT EXISTS(SELECT 1 FROM payment_settlements WHERE payment_id=?)`, paymentID).Scan(&settled); e != nil {
				return e
			}
			if settled {
				return nil
			}
			// A previously confirmed but unsettled payment is safe to settle.
		} else if status != "pending" {
			return ErrPaymentState
		}

		if status == "pending" {
			res, e := tx.Exec(`UPDATE payments SET status='confirmed',provider_ref=?,provider_event_id=?,updated_at=? WHERE id=? AND status='pending'`, providerRef, eventID, at, paymentID)
			if e != nil {
				return e
			}
			n, _ := res.RowsAffected()
			if n != 1 {
				return ErrPaymentState
			}
			ref = providerRef
			oldEvent = eventID
		}

		var already bool
		if e := tx.QueryRow(`SELECT EXISTS(SELECT 1 FROM payment_settlements WHERE payment_id=?)`, paymentID).Scan(&already); e != nil {
			return e
		}
		if already {
			return nil
		}

		first, second := clearingAccountID, account
		if first > second {
			first, second = second, first
		}
		var dummy uint64
		if e := Database.QueryRowForUpdate(tx, `SELECT account_id FROM financial_balances WHERE account_id=?`, first).Scan(&dummy); e != nil {
			return e
		}
		if second != first {
			if e := Database.QueryRowForUpdate(tx, `SELECT account_id FROM financial_balances WHERE account_id=?`, second).Scan(&dummy); e != nil {
				return e
			}
		}

		var sourceCurrency, destCurrency, sourceStatus, destStatus string
		if e := tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=?`, clearingAccountID).Scan(&sourceCurrency, &sourceStatus); e != nil {
			return e
		}
		if e := tx.QueryRow(`SELECT currency,status FROM financial_accounts WHERE id=?`, account).Scan(&destCurrency, &destStatus); e != nil {
			return e
		}
		if sourceCurrency != currency || destCurrency != currency {
			return errors.New("settlement currency mismatch")
		}
		if sourceStatus != "active" || destStatus != "active" {
			return errors.New("settlement account inactive")
		}
		var available uint64
		if e := tx.QueryRow(`SELECT available_cents FROM financial_balances WHERE account_id=? FOR UPDATE`, clearingAccountID).Scan(&available); e != nil {
			return e
		}
		if available < amount {
			return errors.New("provider clearing balance insufficient")
		}

		var txID uint64
		err = tx.QueryRow(`SELECT id FROM ledger_transactions WHERE idempotency_key=?`, idem).Scan(&txID)
		if err != nil && !errors.Is(err, sql.ErrNoRows) {
			return err
		}
		if errors.Is(err, sql.ErrNoRows) {
			res, e := tx.Exec(`INSERT INTO ledger_transactions (public_id,idempotency_key,currency,description,created_at) VALUES (?,?,?,?,?)`,
				newID(), idem, currency, fmt.Sprintf("PSP settlement %s:%s", provider, ref), at)
			if e != nil {
				return e
			}
			id, e := res.LastInsertId()
			if e != nil {
				return e
			}
			txID = uint64(id)
			if _, e = tx.Exec(`INSERT INTO ledger_entries (transaction_id,account_id,debit_cents,credit_cents,created_at) VALUES (?,?,?,?,?),(?,?,?,?,?)`,
				txID, clearingAccountID, amount, 0, at, txID, account, 0, amount, at); e != nil {
				return e
			}
		} else {
			var cnt int
			if e := tx.QueryRow(`SELECT COUNT(*) FROM ledger_entries WHERE transaction_id=?`, txID).Scan(&cnt); e != nil {
				return e
			}
			if cnt != 2 {
				return errors.New("settlement idempotency conflict")
			}
		}
		res, e := tx.Exec(`UPDATE financial_balances SET available_cents=available_cents-?,updated_at=? WHERE account_id=? AND available_cents>=?`, amount, at, clearingAccountID, amount)
		if e != nil {
			return e
		}
		n, _ := res.RowsAffected()
		if n != 1 {
			return errors.New("provider clearing balance changed")
		}
		if _, e = tx.Exec(`UPDATE financial_balances SET available_cents=available_cents+?,updated_at=? WHERE account_id=?`, amount, at, account); e != nil {
			return e
		}
		if _, e = tx.Exec(`INSERT INTO payment_settlements (payment_id,ledger_transaction_id,idempotency_key,amount_cents,currency,created_at) VALUES (?,?,?,?,?,?)`,
			paymentID, txID, idem, amount, currency, at); e != nil {
			if strings.Contains(strings.ToLower(e.Error()), "duplicate") {
				return nil
			}
			return e
		}
		return nil
	})
}

func newID() string { return fmt.Sprintf("%x", time.Now().UnixNano()) }
