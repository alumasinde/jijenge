CREATE TABLE provider_earning_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_earning_statuses_code (code),
    UNIQUE KEY uq_provider_earning_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO provider_earning_statuses (code, name, is_terminal) VALUES
('PENDING', 'Pending', 0),
('AVAILABLE', 'Available', 0),
('PROCESSING', 'Processing', 0),
('SETTLED', 'Settled', 1),
('REVERSED', 'Reversed', 1);

CREATE TABLE provider_earnings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    provider_user_id BIGINT UNSIGNED NOT NULL,
    job_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    gross_amount DECIMAL(14,2) NOT NULL,
    platform_fee_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    adjustment_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    net_amount DECIMAL(14,2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    available_at TIMESTAMP NULL,
    settled_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_earnings_public_id (public_id),
    UNIQUE KEY uq_provider_earnings_job (job_id),
    KEY idx_provider_earnings_provider_status (
        provider_user_id, status_id, created_at
    ),
    KEY idx_provider_earnings_available (
        provider_user_id, status_id, available_at
    ),

    CONSTRAINT fk_provider_earnings_provider
        FOREIGN KEY (provider_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_provider_earnings_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_provider_earnings_status
        FOREIGN KEY (status_id)
        REFERENCES provider_earning_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_provider_earnings_amounts
        CHECK (
            gross_amount >= 0
            AND platform_fee_amount >= 0
            AND adjustment_amount >= 0
            AND net_amount >= 0
        )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
