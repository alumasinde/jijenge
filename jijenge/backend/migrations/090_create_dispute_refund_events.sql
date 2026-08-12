CREATE TABLE dispute_event_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(70) NOT NULL,
    name VARCHAR(140) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dispute_event_types_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO dispute_event_types (code,name) VALUES
('OPENED','Opened'),
('UNDER_REVIEW','Under Review'),
('EVIDENCE_ADDED','Evidence Added'),
('RESOLVED','Resolved'),
('CANCELLED','Cancelled');

CREATE TABLE dispute_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    dispute_id BIGINT UNSIGNED NOT NULL,
    event_type_id SMALLINT UNSIGNED NOT NULL,
    actor_user_id BIGINT UNSIGNED NULL,
    notes VARCHAR(2000) NULL,
    metadata_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_dispute_events_dispute (dispute_id,created_at,id),
    CONSTRAINT fk_dispute_events_dispute
        FOREIGN KEY (dispute_id) REFERENCES disputes(id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_dispute_events_type
        FOREIGN KEY (event_type_id) REFERENCES dispute_event_types(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_dispute_events_actor
        FOREIGN KEY (actor_user_id) REFERENCES users(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE refund_event_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(70) NOT NULL,
    name VARCHAR(140) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_refund_event_types_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO refund_event_types (code,name) VALUES
('REQUESTED','Requested'),
('APPROVED','Approved'),
('REJECTED','Rejected'),
('PROCESSING','Processing'),
('PAID','Paid'),
('FAILED','Failed'),
('REVERSED','Reversed');

CREATE TABLE refund_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    refund_id BIGINT UNSIGNED NOT NULL,
    event_type_id SMALLINT UNSIGNED NOT NULL,
    actor_user_id BIGINT UNSIGNED NULL,
    notes VARCHAR(2000) NULL,
    metadata_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_refund_events_refund (refund_id,created_at,id),
    CONSTRAINT fk_refund_events_refund
        FOREIGN KEY (refund_id) REFERENCES refunds(id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_refund_events_type
        FOREIGN KEY (event_type_id) REFERENCES refund_event_types(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_refund_events_actor
        FOREIGN KEY (actor_user_id) REFERENCES users(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
