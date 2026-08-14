
CREATE TABLE payment_settlements (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    payment_id BIGINT UNSIGNED NOT NULL,
    ledger_transaction_id BIGINT UNSIGNED NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    amount_cents BIGINT UNSIGNED NOT NULL,
    currency CHAR(3) NOT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_settlement_payment (payment_id),
    UNIQUE KEY uq_payment_settlement_ledger (ledger_transaction_id),
    UNIQUE KEY uq_payment_settlement_idempotency (idempotency_key),
    CONSTRAINT fk_payment_settlement_payment FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE RESTRICT,
    CONSTRAINT fk_payment_settlement_ledger FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE RESTRICT,
    CONSTRAINT chk_payment_settlement_amount CHECK (amount_cents > 0)
) ENGINE=InnoDB;
