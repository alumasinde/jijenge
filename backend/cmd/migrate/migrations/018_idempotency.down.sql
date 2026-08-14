ALTER TABLE settlements
    DROP INDEX uq_settlement_idempotency_user,
    DROP COLUMN idempotency_key;

ALTER TABLE escrow_payments
    DROP INDEX uq_escrow_idempotency_user,
    DROP COLUMN idempotency_key;
