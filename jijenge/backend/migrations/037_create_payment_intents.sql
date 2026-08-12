CREATE TABLE payment_intents (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    job_id BIGINT UNSIGNED NULL,
    payer_user_id BIGINT UNSIGNED NOT NULL,
    payment_method_id SMALLINT UNSIGNED NOT NULL,
    payment_status_id SMALLINT UNSIGNED NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    amount DECIMAL(14,2) NOT NULL,
    description VARCHAR(500) NULL,
    idempotency_key VARCHAR(120) NOT NULL,
    provider_code VARCHAR(80) NULL,
    provider_reference VARCHAR(255) NULL,
    metadata_json JSON NULL,
    expires_at TIMESTAMP NULL,
    succeeded_at TIMESTAMP NULL,
    failed_at TIMESTAMP NULL,
    cancelled_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_intents_public_id (public_id),
    UNIQUE KEY uq_payment_intents_payer_idempotency (
        payer_user_id, idempotency_key
    ),
    KEY idx_payment_intents_job_created (job_id, created_at),
    KEY idx_payment_intents_payer_created (payer_user_id, created_at),
    KEY idx_payment_intents_status_created (
        payment_status_id, created_at
    ),
    KEY idx_payment_intents_provider_reference (
        provider_code, provider_reference
    ),

    CONSTRAINT fk_payment_intents_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_payment_intents_payer
        FOREIGN KEY (payer_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_payment_intents_method
        FOREIGN KEY (payment_method_id)
        REFERENCES payment_methods (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_payment_intents_status
        FOREIGN KEY (payment_status_id)
        REFERENCES payment_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_payment_intents_amount
        CHECK (amount > 0),

    CONSTRAINT chk_payment_intents_currency
        CHECK (CHAR_LENGTH(currency_code) = 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
