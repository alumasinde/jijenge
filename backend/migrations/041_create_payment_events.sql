CREATE TABLE payment_event_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(150) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,

    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_event_types_code (code),
    UNIQUE KEY uq_payment_event_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO payment_event_types (code, name) VALUES
('PAYMENT_CREATED', 'Payment Created'),
('PAYMENT_PROVIDER_REQUESTED', 'Payment Provider Requested'),
('PAYMENT_CALLBACK_RECEIVED', 'Payment Callback Received'),
('PAYMENT_SUCCEEDED', 'Payment Succeeded'),
('PAYMENT_FAILED', 'Payment Failed'),
('PAYMENT_CANCELLED', 'Payment Cancelled'),
('PAYMENT_REFUNDED', 'Payment Refunded');

CREATE TABLE payment_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    payment_intent_id BIGINT UNSIGNED NOT NULL,
    payment_event_type_id SMALLINT UNSIGNED NOT NULL,
    provider_code VARCHAR(80) NULL,
    provider_event_id VARCHAR(255) NULL,
    event_key VARCHAR(180) NOT NULL,
    payload_hash CHAR(64) NULL,
    payload_json JSON NULL,
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_events_event_key (event_key),
    KEY idx_payment_events_intent_created (
        payment_intent_id, created_at
    ),
    KEY idx_payment_events_provider_event (
        provider_code, provider_event_id
    ),

    CONSTRAINT fk_payment_events_intent
        FOREIGN KEY (payment_intent_id)
        REFERENCES payment_intents (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_payment_events_type
        FOREIGN KEY (payment_event_type_id)
        REFERENCES payment_event_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
