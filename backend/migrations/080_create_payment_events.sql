CREATE TABLE job_payment_event_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(70) NOT NULL,
    name VARCHAR(140) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_job_payment_event_types_code (code),
    UNIQUE KEY uq_job_payment_event_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO job_payment_event_types (code,name) VALUES
('CREATED','Created'),
('PAYMENT_INTENT_CREATED','Payment Intent Created'),
('PAYMENT_SUCCEEDED','Payment Succeeded'),
('PAYMENT_FAILED','Payment Failed'),
('REFUNDED','Refunded'),
('PAYOUT_REQUESTED','Payout Requested'),
('PAYOUT_PAID','Payout Paid');

CREATE TABLE job_payment_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_payment_record_id BIGINT UNSIGNED NOT NULL,
    event_type_id SMALLINT UNSIGNED NOT NULL,
    actor_user_id BIGINT UNSIGNED NULL,
    notes VARCHAR(2000) NULL,
    metadata_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_job_payment_events_record_created
        (job_payment_record_id,created_at,id),
    CONSTRAINT fk_job_payment_events_record
        FOREIGN KEY (job_payment_record_id) REFERENCES job_payment_records(id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_job_payment_events_type
        FOREIGN KEY (event_type_id) REFERENCES job_payment_event_types(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_job_payment_events_actor
        FOREIGN KEY (actor_user_id) REFERENCES users(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
