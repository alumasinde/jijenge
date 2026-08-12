CREATE TABLE provider_settlement_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_settlement_statuses_code (code),
    UNIQUE KEY uq_provider_settlement_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO provider_settlement_statuses
    (code,name,is_terminal,is_success)
VALUES
('PENDING','Pending',0,0),
('ON_HOLD','On Hold',0,0),
('AVAILABLE','Available',0,0),
('REQUESTED','Requested',0,0),
('PROCESSING','Processing',0,0),
('PAID','Paid',1,1),
('FAILED','Failed',1,0),
('CANCELLED','Cancelled',1,0),
('REVERSED','Reversed',1,0);

CREATE TABLE provider_settlements (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    provider_id BIGINT UNSIGNED NOT NULL,
    assignment_id BIGINT UNSIGNED NOT NULL,
    provider_earning_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    payout_method_id SMALLINT UNSIGNED NULL,
    payout_reference VARCHAR(255) NULL,
    requested_at TIMESTAMP NULL,
    processing_at TIMESTAMP NULL,
    paid_at TIMESTAMP NULL,
    failure_reason VARCHAR(1000) NULL,
    idempotency_key VARCHAR(160) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_settlements_public_id (public_id),
    UNIQUE KEY uq_provider_settlements_earning (provider_earning_id),
    UNIQUE KEY uq_provider_settlements_idempotency (provider_id,idempotency_key),
    KEY idx_provider_settlements_provider_status (provider_id,status_id,created_at),
    KEY idx_provider_settlements_status_created (status_id,created_at,id),

    CONSTRAINT fk_provider_settlements_provider
        FOREIGN KEY (provider_id) REFERENCES provider_profiles(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_provider_settlements_assignment
        FOREIGN KEY (assignment_id) REFERENCES job_assignments(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_provider_settlements_earning
        FOREIGN KEY (provider_earning_id) REFERENCES provider_earnings(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_provider_settlements_status
        FOREIGN KEY (status_id) REFERENCES provider_settlement_statuses(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_provider_settlements_payout_method
        FOREIGN KEY (payout_method_id) REFERENCES payment_methods(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
