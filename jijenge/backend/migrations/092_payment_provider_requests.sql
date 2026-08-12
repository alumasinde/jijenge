CREATE TABLE payment_provider_request_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_provider_request_statuses_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO payment_provider_request_statuses (code,name,is_terminal) VALUES
('CREATED','Created',0),
('SENT','Sent',0),
('SUCCEEDED','Succeeded',1),
('FAILED','Failed',1),
('TIMEOUT','Timeout',1),
('CANCELLED','Cancelled',1);

CREATE TABLE payment_provider_requests (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    provider_code VARCHAR(40) NOT NULL,
    operation_code VARCHAR(70) NOT NULL,
    payment_intent_id BIGINT UNSIGNED NULL,
    payment_transaction_id BIGINT UNSIGNED NULL,
    refund_id BIGINT UNSIGNED NULL,
    settlement_id BIGINT UNSIGNED NULL,
    idempotency_key VARCHAR(160) NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    provider_request_id VARCHAR(255) NULL,
    provider_reference VARCHAR(255) NULL,
    request_hash CHAR(64) NULL,
    response_json JSON NULL,
    failure_reason VARCHAR(1000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_provider_requests_public_id (public_id),
    UNIQUE KEY uq_payment_provider_requests_idempotency (
        provider_code,operation_code,idempotency_key
    ),
    KEY idx_payment_provider_requests_intent (
        payment_intent_id,status_id,created_at
    ),
    KEY idx_payment_provider_requests_ref (
        provider_code,provider_reference
    ),
    CONSTRAINT fk_payment_provider_requests_status
        FOREIGN KEY (status_id) REFERENCES payment_provider_request_statuses(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_payment_provider_requests_intent
        FOREIGN KEY (payment_intent_id) REFERENCES payment_intents(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_payment_provider_requests_transaction
        FOREIGN KEY (payment_transaction_id) REFERENCES payment_transactions(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_payment_provider_requests_refund
        FOREIGN KEY (refund_id) REFERENCES refunds(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_payment_provider_requests_settlement
        FOREIGN KEY (settlement_id) REFERENCES provider_settlements(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
