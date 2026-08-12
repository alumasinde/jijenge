CREATE TABLE job_applications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_id BIGINT UNSIGNED NOT NULL,
    provider_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    proposed_price DECIMAL(12,2) NULL,
    message VARCHAR(2000) NULL,
    estimated_start_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    responded_at TIMESTAMP NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_job_applications_job_provider (job_id, provider_id),
    KEY idx_job_applications_job_status_created (job_id, status_id, created_at),
    KEY idx_job_applications_provider_status_created (provider_id, status_id, created_at),
    KEY idx_job_applications_status_created (status_id, created_at),

    CONSTRAINT fk_job_applications_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_job_applications_provider
        FOREIGN KEY (provider_id)
        REFERENCES provider_profiles (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_job_applications_status
        FOREIGN KEY (status_id)
        REFERENCES job_application_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_job_applications_price
        CHECK (proposed_price IS NULL OR proposed_price >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
