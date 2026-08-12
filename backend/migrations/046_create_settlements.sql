CREATE TABLE settlement_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_settlement_statuses_code (code),
    UNIQUE KEY uq_settlement_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO settlement_statuses
    (code, name, is_terminal, is_success)
VALUES
('PENDING', 'Pending', 0, 0),
('PROCESSING', 'Processing', 0, 0),
('SUCCEEDED', 'Succeeded', 1, 1),
('FAILED', 'Failed', 1, 0),
('CANCELLED', 'Cancelled', 1, 0);

CREATE TABLE settlements (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    provider_user_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    destination_type VARCHAR(50) NOT NULL,
    destination_reference VARCHAR(255) NULL,
    provider_code VARCHAR(80) NULL,
    provider_reference VARCHAR(255) NULL,
    idempotency_key VARCHAR(160) NOT NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    failure_reason VARCHAR(1000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_settlements_public_id (public_id),
    UNIQUE KEY uq_settlements_provider_idempotency (
        provider_user_id, idempotency_key
    ),
    KEY idx_settlements_provider_status_created (
        provider_user_id, status_id, created_at
    ),
    KEY idx_settlements_provider_reference (
        provider_code, provider_reference
    ),

    CONSTRAINT fk_settlements_provider
        FOREIGN KEY (provider_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_settlements_status
        FOREIGN KEY (status_id)
        REFERENCES settlement_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_settlements_amount
        CHECK (amount > 0),

    CONSTRAINT chk_settlements_currency
        CHECK (CHAR_LENGTH(currency_code) = 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE settlement_items (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    settlement_id BIGINT UNSIGNED NOT NULL,
    provider_earning_id BIGINT UNSIGNED NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_settlement_items_earning (provider_earning_id),
    KEY idx_settlement_items_settlement (settlement_id, id),

    CONSTRAINT fk_settlement_items_settlement
        FOREIGN KEY (settlement_id)
        REFERENCES settlements (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_settlement_items_earning
        FOREIGN KEY (provider_earning_id)
        REFERENCES provider_earnings (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_settlement_items_amount
        CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
