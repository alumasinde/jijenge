CREATE TABLE reconciliation_job_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_reconciliation_job_statuses_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO reconciliation_job_statuses (code,name) VALUES ('RUNNING','Running'),('COMPLETED','Completed'),('FAILED','Failed');
CREATE TABLE reconciliation_jobs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    provider_code VARCHAR(40) NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    scanned_count INT UNSIGNED NOT NULL DEFAULT 0,
    matched_count INT UNSIGNED NOT NULL DEFAULT 0,
    exception_count INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    failure_reason VARCHAR(2000) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_reconciliation_jobs_public_id (public_id),
    KEY idx_reconciliation_jobs_provider_status (provider_code,status_id,created_at),
    CONSTRAINT fk_reconciliation_jobs_status FOREIGN KEY (status_id) REFERENCES reconciliation_job_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
