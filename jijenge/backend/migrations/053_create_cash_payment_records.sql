CREATE TABLE cash_payment_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_cash_payment_statuses_code (code),
    UNIQUE KEY uq_cash_payment_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO cash_payment_statuses
    (code, name, is_terminal, is_success)
VALUES
('PENDING_CONFIRMATION', 'Pending Confirmation', 0, 0),
('CONFIRMED', 'Confirmed', 1, 1),
('REJECTED', 'Rejected', 1, 0),
('CANCELLED', 'Cancelled', 1, 0);

CREATE TABLE cash_payment_records (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    payment_intent_id BIGINT UNSIGNED NOT NULL,
    payer_user_id BIGINT UNSIGNED NOT NULL,
    recorded_by_user_id BIGINT UNSIGNED NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    receipt_reference VARCHAR(120) NULL,
    confirmation_notes VARCHAR(1000) NULL,
    confirmed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_cash_payment_records_public_id (public_id),
    UNIQUE KEY uq_cash_payment_records_intent (payment_intent_id),
    KEY idx_cash_payment_records_payer_status (
        payer_user_id, status_id, created_at
    ),
    KEY idx_cash_payment_records_receipt (receipt_reference),

    CONSTRAINT fk_cash_payment_records_intent
        FOREIGN KEY (payment_intent_id)
        REFERENCES payment_intents (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_cash_payment_records_payer
        FOREIGN KEY (payer_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_cash_payment_records_recorder
        FOREIGN KEY (recorded_by_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_cash_payment_records_status
        FOREIGN KEY (status_id)
        REFERENCES cash_payment_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_cash_payment_records_amount
        CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
