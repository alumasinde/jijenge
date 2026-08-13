CREATE TABLE payment_reconciliation_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_reconciliation_statuses_code (code),
    UNIQUE KEY uq_payment_reconciliation_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO payment_reconciliation_statuses (code,name) VALUES ('UNMATCHED','Unmatched'),('MATCHED','Matched'),('EXCEPTION','Exception'),('RESOLVED','Resolved');
CREATE TABLE payment_reconciliation_records (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    payment_transaction_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    provider_code VARCHAR(40) NOT NULL,
    provider_transaction_id VARCHAR(255) NULL,
    provider_reference VARCHAR(255) NULL,
    provider_amount DECIMAL(14,2) NULL,
    provider_currency CHAR(3) NULL,
    mismatch_reason VARCHAR(1000) NULL,
    checked_at TIMESTAMP NULL,
    resolved_at TIMESTAMP NULL,
    resolved_by_user_id BIGINT UNSIGNED NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_reconciliation_transaction (payment_transaction_id),
    KEY idx_payment_reconciliation_status (status_id,created_at,id),
    KEY idx_payment_reconciliation_provider_ref (provider_code,provider_reference),
    CONSTRAINT fk_payment_reconciliation_transaction FOREIGN KEY (payment_transaction_id) REFERENCES payment_transactions(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_payment_reconciliation_status FOREIGN KEY (status_id) REFERENCES payment_reconciliation_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_payment_reconciliation_resolver FOREIGN KEY (resolved_by_user_id) REFERENCES users(id) ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
