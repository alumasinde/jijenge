CREATE TABLE payment_webhook_receipts (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider_code VARCHAR(80) NOT NULL,
    provider_event_id VARCHAR(255) NULL,
    event_key VARCHAR(180) NOT NULL,
    payload_hash CHAR(64) NOT NULL,
    signature_verified TINYINT(1) NOT NULL DEFAULT 0,
    processing_status VARCHAR(40) NOT NULL DEFAULT 'RECEIVED',
    payload_json JSON NOT NULL,
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_webhook_receipts_event_key (event_key),
    KEY idx_payment_webhook_receipts_provider_event (
        provider_code, provider_event_id
    ),
    KEY idx_payment_webhook_receipts_status_received (
        processing_status, received_at
    ),
    KEY idx_payment_webhook_receipts_hash (
        payload_hash
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
