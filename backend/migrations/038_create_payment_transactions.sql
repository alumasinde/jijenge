CREATE TABLE payment_transactions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    payment_intent_id BIGINT UNSIGNED NOT NULL,
    payment_status_id SMALLINT UNSIGNED NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency_code CHAR(3) NOT NULL,
    provider_code VARCHAR(80) NULL,
    provider_transaction_id VARCHAR(255) NULL,
    provider_reference VARCHAR(255) NULL,
    provider_response_code VARCHAR(100) NULL,
    provider_response_message VARCHAR(1000) NULL,
    idempotency_key VARCHAR(120) NOT NULL,
    raw_response_json JSON NULL,
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_transactions_public_id (public_id),
    UNIQUE KEY uq_payment_transactions_idempotency (
        payment_intent_id, idempotency_key
    ),
    KEY idx_payment_transactions_intent_created (
        payment_intent_id, created_at
    ),
    KEY idx_payment_transactions_provider_tx (
        provider_code, provider_transaction_id
    ),
    KEY idx_payment_transactions_status_created (
        payment_status_id, created_at
    ),

    CONSTRAINT fk_payment_transactions_intent
        FOREIGN KEY (payment_intent_id)
        REFERENCES payment_intents (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_payment_transactions_status
        FOREIGN KEY (payment_status_id)
        REFERENCES payment_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_payment_transactions_amount
        CHECK (amount > 0),

    CONSTRAINT chk_payment_transactions_currency
        CHECK (CHAR_LENGTH(currency_code) = 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE payment_transaction_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,

    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_transaction_types_code (code),
    UNIQUE KEY uq_payment_transaction_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO payment_transaction_types (code, name) VALUES
('CHARGE', 'Charge'),
('REFUND', 'Refund'),
('ADJUSTMENT', 'Adjustment');
