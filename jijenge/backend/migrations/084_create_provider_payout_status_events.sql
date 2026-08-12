CREATE TABLE provider_payout_event_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(70) NOT NULL,
    name VARCHAR(140) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_payout_event_types_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO provider_payout_event_types (code,name) VALUES
('REQUESTED','Requested'),
('APPROVED','Approved'),
('REJECTED','Rejected'),
('PROCESSING','Processing'),
('PAID','Paid'),
('FAILED','Failed'),
('REVERSED','Reversed');

CREATE TABLE provider_payout_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    settlement_id BIGINT UNSIGNED NOT NULL,
    event_type_id SMALLINT UNSIGNED NOT NULL,
    actor_user_id BIGINT UNSIGNED NULL,
    notes VARCHAR(2000) NULL,
    metadata_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_provider_payout_events_settlement (
        settlement_id,created_at,id
    ),
    CONSTRAINT fk_provider_payout_events_settlement
        FOREIGN KEY (settlement_id) REFERENCES provider_settlements(id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_provider_payout_events_type
        FOREIGN KEY (event_type_id) REFERENCES provider_payout_event_types(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_provider_payout_events_actor
        FOREIGN KEY (actor_user_id) REFERENCES users(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
