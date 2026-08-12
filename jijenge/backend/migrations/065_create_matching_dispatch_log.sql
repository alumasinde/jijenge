CREATE TABLE matching_dispatch_logs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_id BIGINT UNSIGNED NOT NULL,
    dispatch_key VARCHAR(180) NOT NULL,
    radius_km DECIMAL(8,2) NOT NULL,
    candidate_count INT UNSIGNED NOT NULL DEFAULT 0,
    notified_count INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_matching_dispatch_logs_key (dispatch_key),
    KEY idx_matching_dispatch_logs_job_created (job_id, created_at),

    CONSTRAINT fk_matching_dispatch_logs_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
