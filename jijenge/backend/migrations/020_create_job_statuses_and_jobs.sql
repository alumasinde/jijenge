CREATE TABLE job_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_job_statuses_code (code),
    UNIQUE KEY uq_job_statuses_name (name),
    KEY idx_job_statuses_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO job_statuses (code, name, description, sort_order) VALUES
('DRAFT', 'Draft', 'Job has not yet been published.', 10),
('OPEN', 'Open', 'Job is accepting provider applications.', 20),
('ASSIGNED', 'Assigned', 'A provider has been selected.', 30),
('IN_PROGRESS', 'In Progress', 'The provider is working on the job.', 40),
('COMPLETED', 'Completed', 'The job has been completed.', 50),
('CANCELLED', 'Cancelled', 'The job has been cancelled.', 60);

CREATE TABLE jobs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_id BIGINT UNSIGNED NOT NULL,
    service_id INT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    budget_min DECIMAL(12,2) NULL,
    budget_max DECIMAL(12,2) NULL,
    preferred_start_at DATETIME NULL,
    preferred_end_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    cancelled_at TIMESTAMP NULL,

    PRIMARY KEY (id),
    KEY idx_jobs_customer_created (customer_id, created_at),
    KEY idx_jobs_service_status_created (service_id, status_id, created_at),
    KEY idx_jobs_status_created (status_id, created_at),
    KEY idx_jobs_preferred_start (preferred_start_at),

    CONSTRAINT fk_jobs_customer
        FOREIGN KEY (customer_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_jobs_service
        FOREIGN KEY (service_id)
        REFERENCES services (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_jobs_status
        FOREIGN KEY (status_id)
        REFERENCES job_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_jobs_budget_min
        CHECK (budget_min IS NULL OR budget_min >= 0),

    CONSTRAINT chk_jobs_budget_max
        CHECK (budget_max IS NULL OR budget_max >= 0),

    CONSTRAINT chk_jobs_budget_order
        CHECK (
            budget_min IS NULL
            OR budget_max IS NULL
            OR budget_max >= budget_min
        )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
