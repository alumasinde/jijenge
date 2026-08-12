CREATE TABLE refund_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_refund_statuses_code (code),
    UNIQUE KEY uq_refund_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO refund_statuses
    (code, name, is_terminal, is_success)
VALUES
('REQUESTED', 'Requested', 0, 0),
('PROCESSING', 'Processing', 0, 0),
('SUCCEEDED', 'Succeeded', 1, 1),
('FAILED', 'Failed', 1, 0),
('CANCELLED', 'Cancelled', 1, 0);

CREATE TABLE refunds (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    payment_intent_id BIGINT UNSIGNED NOT NULL,
    payment_transaction_id BIGINT UNSIGNED NULL,
    requested_by_user_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    reason VARCHAR(1000) NULL,
    provider_code VARCHAR(80) NULL,
    provider_reference VARCHAR(255) NULL,
    idempotency_key VARCHAR(160) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_refunds_public_id (public_id),
    UNIQUE KEY uq_refunds_requester_idempotency (
        requested_by_user_id, idempotency_key
    ),
    KEY idx_refunds_intent_status_created (
        payment_intent_id, status_id, created_at
    ),
    KEY idx_refunds_requester_created (
        requested_by_user_id, created_at
    ),
    KEY idx_refunds_provider_reference (
        provider_code, provider_reference
    ),

    CONSTRAINT fk_refunds_payment_intent
        FOREIGN KEY (payment_intent_id)
        REFERENCES payment_intents (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_refunds_payment_transaction
        FOREIGN KEY (payment_transaction_id)
        REFERENCES payment_transactions (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_refunds_requester
        FOREIGN KEY (requested_by_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_refunds_status
        FOREIGN KEY (status_id)
        REFERENCES refund_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_refunds_amount
        CHECK (amount > 0),

    CONSTRAINT chk_refunds_currency
        CHECK (CHAR_LENGTH(currency_code) = 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
