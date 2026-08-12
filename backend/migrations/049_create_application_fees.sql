CREATE TABLE application_fee_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_application_fee_statuses_code (code),
    UNIQUE KEY uq_application_fee_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO application_fee_statuses
    (code, name, is_terminal, is_success)
VALUES
('PENDING', 'Pending', 0, 0),
('PAID', 'Paid', 1, 1),
('FAILED', 'Failed', 1, 0),
('CANCELLED', 'Cancelled', 1, 0),
('WAIVED', 'Waived', 1, 1);

CREATE TABLE application_fees (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    application_id BIGINT UNSIGNED NOT NULL,
    payer_user_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    payment_intent_id BIGINT UNSIGNED NULL,
    payment_method_id SMALLINT UNSIGNED NULL,
    idempotency_key VARCHAR(160) NOT NULL,
    due_at TIMESTAMP NULL,
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_application_fees_public_id (public_id),
    UNIQUE KEY uq_application_fees_application (application_id),
    UNIQUE KEY uq_application_fees_payer_idempotency (
        payer_user_id, idempotency_key
    ),
    KEY idx_application_fees_payer_status (
        payer_user_id, status_id, created_at
    ),
    KEY idx_application_fees_payment_intent (payment_intent_id),

    CONSTRAINT fk_application_fees_application
        FOREIGN KEY (application_id)
        REFERENCES job_applications (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_application_fees_payer
        FOREIGN KEY (payer_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_application_fees_status
        FOREIGN KEY (status_id)
        REFERENCES application_fee_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_application_fees_payment_intent
        FOREIGN KEY (payment_intent_id)
        REFERENCES payment_intents (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_application_fees_payment_method
        FOREIGN KEY (payment_method_id)
        REFERENCES payment_methods (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT chk_application_fees_amount
        CHECK (amount >= 0),

    CONSTRAINT chk_application_fees_currency
        CHECK (CHAR_LENGTH(currency_code) = 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
