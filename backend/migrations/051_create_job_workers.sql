CREATE TABLE worker_job_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(40) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_worker_job_statuses_code (code),
    UNIQUE KEY uq_worker_job_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO worker_job_statuses (code, name) VALUES
('PENDING', 'Pending'),
('PROCESSING', 'Processing'),
('SUCCEEDED', 'Succeeded'),
('FAILED', 'Failed'),
('DEAD_LETTER', 'Dead Letter');

CREATE TABLE worker_jobs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_key VARCHAR(180) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    payload_json JSON NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    attempt_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    max_attempts SMALLINT UNSIGNED NOT NULL DEFAULT 5,
    available_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    locked_at TIMESTAMP NULL,
    locked_by VARCHAR(120) NULL,
    last_error VARCHAR(2000) NULL,
    succeeded_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_worker_jobs_key (job_key),
    KEY idx_worker_jobs_claim (
        status_id, available_at, id
    ),
    KEY idx_worker_jobs_locked (
        locked_at, status_id
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
