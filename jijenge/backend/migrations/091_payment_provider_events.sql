CREATE TABLE payment_provider_event_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_provider_event_statuses_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO payment_provider_event_statuses (code,name) VALUES
('RECEIVED','Received'),
('PROCESSED','Processed'),
('DUPLICATE','Duplicate'),
('REJECTED','Rejected'),
('FAILED','Failed');

CREATE TABLE payment_provider_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    provider_code VARCHAR(40) NOT NULL,
    provider_event_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    payment_intent_id BIGINT UNSIGNED NULL,
    payment_transaction_id BIGINT UNSIGNED NULL,
    payload_hash CHAR(64) NOT NULL,
    payload_json JSON NOT NULL,
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    failure_reason VARCHAR(1000) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_provider_events_event (
        provider_code,provider_event_id
    ),
    UNIQUE KEY uq_payment_provider_events_payload (
        provider_code,payload_hash
    ),
    KEY idx_payment_provider_events_intent (
        payment_intent_id,received_at,id
    ),
    KEY idx_payment_provider_events_transaction (
        payment_transaction_id,received_at,id
    ),
    CONSTRAINT fk_payment_provider_events_status
        FOREIGN KEY (status_id) REFERENCES payment_provider_event_statuses(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_payment_provider_events_intent
        FOREIGN KEY (payment_intent_id) REFERENCES payment_intents(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_payment_provider_events_transaction
        FOREIGN KEY (payment_transaction_id) REFERENCES payment_transactions(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
