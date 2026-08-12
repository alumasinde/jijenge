CREATE TABLE job_assignments (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_id BIGINT UNSIGNED NOT NULL,
    provider_id BIGINT UNSIGNED NOT NULL,
    application_id BIGINT UNSIGNED NULL,
    assigned_by_user_id BIGINT UNSIGNED NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    cancelled_at TIMESTAMP NULL,
    cancellation_reason VARCHAR(1000) NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_job_assignments_job (job_id),
    KEY idx_job_assignments_provider_status (provider_id, cancelled_at, completed_at),
    KEY idx_job_assignments_assigned_by (assigned_by_user_id),

    CONSTRAINT fk_job_assignments_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_job_assignments_provider
        FOREIGN KEY (provider_id)
        REFERENCES provider_profiles (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_job_assignments_application
        FOREIGN KEY (application_id)
        REFERENCES job_applications (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_job_assignments_assigned_by
        FOREIGN KEY (assigned_by_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
