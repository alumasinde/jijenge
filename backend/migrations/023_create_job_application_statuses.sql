CREATE TABLE job_application_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_job_application_statuses_code (code),
    UNIQUE KEY uq_job_application_statuses_name (name),
    KEY idx_job_application_statuses_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO job_application_statuses (code, name, description, sort_order) VALUES
('PENDING', 'Pending', 'Provider application is awaiting customer decision.', 10),
('ACCEPTED', 'Accepted', 'Application was accepted for the job.', 20),
('REJECTED', 'Rejected', 'Application was rejected by the customer.', 30),
('WITHDRAWN', 'Withdrawn', 'Provider withdrew the application.', 40),
('CANCELLED', 'Cancelled', 'Application was cancelled because the job was assigned or closed.', 50);
