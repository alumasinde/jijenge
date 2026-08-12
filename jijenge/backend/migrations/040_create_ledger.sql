CREATE TABLE ledger_entry_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,

    PRIMARY KEY (id),
    UNIQUE KEY uq_ledger_entry_types_code (code),
    UNIQUE KEY uq_ledger_entry_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO ledger_entry_types (code, name) VALUES
('PAYMENT_CAPTURE', 'Payment Capture'),
('PROVIDER_EARNING', 'Provider Earning'),
('PLATFORM_FEE', 'Platform Fee'),
('REFUND', 'Refund'),
('SETTLEMENT', 'Settlement'),
('ADJUSTMENT', 'Adjustment');

CREATE TABLE ledger_transactions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    reference_type VARCHAR(80) NOT NULL,
    reference_id BIGINT UNSIGNED NOT NULL,
    payment_transaction_id BIGINT UNSIGNED NULL,
    entry_type_id SMALLINT UNSIGNED NOT NULL,
    currency_code CHAR(3) NOT NULL,
    description VARCHAR(500) NULL,
    idempotency_key VARCHAR(160) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_ledger_transactions_public_id (public_id),
    UNIQUE KEY uq_ledger_transactions_idempotency (idempotency_key),
    KEY idx_ledger_transactions_reference (
        reference_type, reference_id, created_at
    ),
    KEY idx_ledger_transactions_payment (
        payment_transaction_id, created_at
    ),
    KEY idx_ledger_transactions_entry_type (
        entry_type_id, created_at
    ),

    CONSTRAINT fk_ledger_transactions_payment
        FOREIGN KEY (payment_transaction_id)
        REFERENCES payment_transactions (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_ledger_transactions_entry_type
        FOREIGN KEY (entry_type_id)
        REFERENCES ledger_entry_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_ledger_transactions_currency
        CHECK (CHAR_LENGTH(currency_code) = 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ledger_lines (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ledger_transaction_id BIGINT UNSIGNED NOT NULL,
    financial_account_id BIGINT UNSIGNED NOT NULL,
    debit_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    credit_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_ledger_lines_transaction (ledger_transaction_id, id),
    KEY idx_ledger_lines_account_created (
        financial_account_id, created_at, id
    ),

    CONSTRAINT fk_ledger_lines_transaction
        FOREIGN KEY (ledger_transaction_id)
        REFERENCES ledger_transactions (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_ledger_lines_account
        FOREIGN KEY (financial_account_id)
        REFERENCES financial_accounts (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_ledger_lines_amounts
        CHECK (
            (debit_amount > 0 AND credit_amount = 0)
            OR
            (credit_amount > 0 AND debit_amount = 0)
        )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
