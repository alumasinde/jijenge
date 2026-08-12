CREATE TABLE job_financial_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_job_financial_statuses_code (code),
    UNIQUE KEY uq_job_financial_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO job_financial_statuses (code, name, is_terminal) VALUES
('NOT_READY', 'Not Ready', 0),
('PENDING_PAYMENT', 'Pending Payment', 0),
('PAID', 'Paid', 1),
('REFUNDED', 'Refunded', 1),
('PARTIALLY_REFUNDED', 'Partially Refunded', 0),
('CANCELLED', 'Cancelled', 1);

CREATE TABLE job_financials (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_id BIGINT UNSIGNED NOT NULL,
    customer_user_id BIGINT UNSIGNED NOT NULL,
    provider_user_id BIGINT UNSIGNED NULL,
    financial_status_id SMALLINT UNSIGNED NOT NULL,
    agreed_amount DECIMAL(14,2) NOT NULL,
    platform_fee_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    payment_processing_fee_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    provider_earning_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    payment_intent_id BIGINT UNSIGNED NULL,
    paid_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_job_financials_job (job_id),
    KEY idx_job_financials_customer_status (
        customer_user_id, financial_status_id, created_at
    ),
    KEY idx_job_financials_provider_status (
        provider_user_id, financial_status_id, created_at
    ),
    KEY idx_job_financials_payment_intent (payment_intent_id),

    CONSTRAINT fk_job_financials_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_job_financials_customer
        FOREIGN KEY (customer_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_job_financials_provider
        FOREIGN KEY (provider_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_job_financials_status
        FOREIGN KEY (financial_status_id)
        REFERENCES job_financial_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_job_financials_payment_intent
        FOREIGN KEY (payment_intent_id)
        REFERENCES payment_intents (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT chk_job_financials_amounts
        CHECK (
            agreed_amount >= 0
            AND platform_fee_amount >= 0
            AND payment_processing_fee_amount >= 0
            AND provider_earning_amount >= 0
        ),

    CONSTRAINT chk_job_financials_currency
        CHECK (CHAR_LENGTH(currency_code) = 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
