ALTER TABLE escrow_payments
    ADD COLUMN idempotency_key VARCHAR(128) NULL AFTER status;

UPDATE escrow_payments
SET idempotency_key = CONCAT('legacy-escrow-', id)
WHERE idempotency_key IS NULL;

ALTER TABLE escrow_payments
    MODIFY COLUMN idempotency_key VARCHAR(128) NOT NULL,
    ADD UNIQUE KEY uq_escrow_idempotency_user (payer_account_id, idempotency_key);

ALTER TABLE settlements
    ADD COLUMN idempotency_key VARCHAR(128) NULL AFTER dispute_reason;

UPDATE settlements
SET idempotency_key = CONCAT('legacy-settlement-', id)
WHERE idempotency_key IS NULL;

ALTER TABLE settlements
    MODIFY COLUMN idempotency_key VARCHAR(128) NOT NULL,
    ADD UNIQUE KEY uq_settlement_idempotency_user (payer_user_id, idempotency_key);
