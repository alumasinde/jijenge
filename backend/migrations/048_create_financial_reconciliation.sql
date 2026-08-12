CREATE TABLE reconciliation_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_reconciliation_statuses_code (code),
    UNIQUE KEY uq_reconciliation_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO reconciliation_statuses
    (code, name, is_terminal, is_success)
VALUES
('OPEN', 'Open', 0, 0),
('MATCHED', 'Matched', 1, 1),
('MISMATCHED', 'Mismatched', 1, 0),
('RESOLVED', 'Resolved', 1, 1);

CREATE TABLE reconciliation_records (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    provider_code VARCHAR(80) NOT NULL,
    provider_reference VARCHAR(255) NULL,
    payment_transaction_id BIGINT UNSIGNED NULL,
    settlement_id BIGINT UNSIGNED NULL,
    expected_amount DECIMAL(14,2) NOT NULL,
    actual_amount DECIMAL(14,2) NULL,
    variance_amount DECIMAL(14,2) NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    status_id SMALLINT UNSIGNED NOT NULL,
    source_event_id VARCHAR(255) NULL,
    notes VARCHAR(2000) NULL,
    reconciled_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_reconciliation_records_public_id (public_id),
    KEY idx_reconciliation_provider_status (
        provider_code, status_id, created_at
    ),
    KEY idx_reconciliation_provider_reference (
        provider_code, provider_reference
    ),
    KEY idx_reconciliation_payment (
        payment_transaction_id
    ),
    KEY idx_reconciliation_settlement (
        settlement_id
    ),

    CONSTRAINT fk_reconciliation_payment
        FOREIGN KEY (payment_transaction_id)
        REFERENCES payment_transactions (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_reconciliation_settlement
        FOREIGN KEY (settlement_id)
        REFERENCES settlements (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_reconciliation_status
        FOREIGN KEY (status_id)
        REFERENCES reconciliation_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_reconciliation_amounts
        CHECK (
            expected_amount >= 0
            AND (actual_amount IS NULL OR actual_amount >= 0)
        ),

    CONSTRAINT chk_reconciliation_currency
        CHECK (CHAR_LENGTH(currency_code) = 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
