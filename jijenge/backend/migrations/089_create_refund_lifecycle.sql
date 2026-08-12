CREATE TABLE refund_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_refund_statuses_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO refund_statuses (code,name,is_terminal,is_success) VALUES
('REQUESTED','Requested',0,0),
('APPROVED','Approved',0,0),
('PROCESSING','Processing',0,0),
('PAID','Paid',1,1),
('FAILED','Failed',1,0),
('REJECTED','Rejected',1,0),
('REVERSED','Reversed',1,0);

CREATE TABLE refunds (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    job_payment_record_id BIGINT UNSIGNED NOT NULL,
    dispute_id BIGINT UNSIGNED NULL,
    requested_by_user_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    requested_amount DECIMAL(14,2) NOT NULL,
    approved_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    paid_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    reason VARCHAR(2000) NULL,
    provider_reference VARCHAR(255) NULL,
    idempotency_key VARCHAR(160) NOT NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP NULL,
    paid_at TIMESTAMP NULL,
    failure_reason VARCHAR(1000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_refunds_public_id (public_id),
    UNIQUE KEY uq_refunds_idempotency (requested_by_user_id,idempotency_key),
    KEY idx_refunds_payment_status (job_payment_record_id,status_id,created_at),
    KEY idx_refunds_dispute (dispute_id,status_id),
    CONSTRAINT fk_refunds_payment
        FOREIGN KEY (job_payment_record_id) REFERENCES job_payment_records(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_refunds_dispute
        FOREIGN KEY (dispute_id) REFERENCES disputes(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_refunds_requester
        FOREIGN KEY (requested_by_user_id) REFERENCES users(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_refunds_status
        FOREIGN KEY (status_id) REFERENCES refund_statuses(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
