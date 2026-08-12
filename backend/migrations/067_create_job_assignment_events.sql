CREATE TABLE assignment_event_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_assignment_event_types_code (code),
    UNIQUE KEY uq_assignment_event_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO assignment_event_types (code, name) VALUES
('ASSIGNED', 'Assigned'),
('CONFIRMED', 'Confirmed'),
('DECLINED', 'Declined'),
('CANCELLED', 'Cancelled'),
('STARTED', 'Started'),
('COMPLETED', 'Completed'),
('FAILED', 'Failed');

CREATE TABLE job_assignment_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    assignment_id BIGINT UNSIGNED NOT NULL,
    event_type_id SMALLINT UNSIGNED NOT NULL,
    actor_user_id BIGINT UNSIGNED NULL,
    notes VARCHAR(1000) NULL,
    metadata_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_job_assignment_events_assignment_created (
        assignment_id, created_at, id
    ),
    KEY idx_job_assignment_events_actor_created (
        actor_user_id, created_at
    ),

    CONSTRAINT fk_job_assignment_events_assignment
        FOREIGN KEY (assignment_id)
        REFERENCES job_assignments (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_job_assignment_events_type
        FOREIGN KEY (event_type_id)
        REFERENCES assignment_event_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_job_assignment_events_actor
        FOREIGN KEY (actor_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
