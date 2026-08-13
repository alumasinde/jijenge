CREATE TABLE financial_execution_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_financial_execution_statuses_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO financial_execution_statuses (code,name,is_terminal,is_success) VALUES ('QUEUED','Queued',0,0),('PROCESSING','Processing',0,0),('SUCCEEDED','Succeeded',1,1),('FAILED','Failed',1,0),('RETRYABLE','Retryable',0,0),('RECONCILIATION_REQUIRED','Reconciliation Required',0,0);
CREATE TABLE financial_executions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    execution_type VARCHAR(60) NOT NULL,
    provider_code VARCHAR(40) NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    refund_id BIGINT UNSIGNED NULL,
    settlement_id BIGINT UNSIGNED NULL,
    provider_request_id BIGINT UNSIGNED NULL,
    attempt_count INT UNSIGNED NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMP NULL,
    provider_reference VARCHAR(255) NULL,
    provider_transaction_id VARCHAR(255) NULL,
    last_error VARCHAR(2000) NULL,
    last_response_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_financial_executions_public_id (public_id),
    KEY idx_financial_executions_queue (status_id,next_attempt_at,id),
    KEY idx_financial_executions_refund (refund_id,status_id,id),
    KEY idx_financial_executions_settlement (settlement_id,status_id,id),
    CONSTRAINT fk_financial_executions_status FOREIGN KEY (status_id) REFERENCES financial_execution_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_financial_executions_refund FOREIGN KEY (refund_id) REFERENCES refunds(id) ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_executions_settlement FOREIGN KEY (settlement_id) REFERENCES provider_settlements(id) ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_executions_provider_request FOREIGN KEY (provider_request_id) REFERENCES payment_provider_requests(id) ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE financial_execution_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    execution_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    attempt_number INT UNSIGNED NOT NULL,
    provider_reference VARCHAR(255) NULL,
    provider_transaction_id VARCHAR(255) NULL,
    response_json JSON NULL,
    error_message VARCHAR(2000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_financial_execution_events_execution (execution_id,created_at,id),
    CONSTRAINT fk_financial_execution_events_execution FOREIGN KEY (execution_id) REFERENCES financial_executions(id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_financial_execution_events_status FOREIGN KEY (status_id) REFERENCES financial_execution_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
