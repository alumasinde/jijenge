CREATE TABLE job_execution_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_job_execution_statuses_code (code),
    UNIQUE KEY uq_job_execution_statuses_name (name),
    KEY idx_job_execution_statuses_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO job_execution_statuses
    (code, name, is_terminal, is_success, sort_order)
VALUES
('ASSIGNED', 'Assigned', 0, 0, 10),
('ON_THE_WAY', 'On The Way', 0, 0, 20),
('ARRIVED', 'Arrived', 0, 0, 30),
('IN_PROGRESS', 'In Progress', 0, 0, 40),
('PAUSED', 'Paused', 0, 0, 50),
('COMPLETED_PENDING_CONFIRMATION', 'Completed Pending Confirmation', 0, 0, 60),
('COMPLETED', 'Completed', 1, 1, 70),
('CANCELLED', 'Cancelled', 1, 0, 80),
('DISPUTED', 'Disputed', 0, 0, 90),
('FAILED', 'Failed', 1, 0, 100);

ALTER TABLE job_assignments
    ADD COLUMN execution_status_id SMALLINT UNSIGNED NULL AFTER status_id,
    ADD COLUMN customer_confirmation_deadline TIMESTAMP NULL AFTER completed_at;

UPDATE job_assignments ja
INNER JOIN job_execution_statuses jes ON jes.code = 'ASSIGNED'
SET ja.execution_status_id = jes.id;

ALTER TABLE job_assignments
    MODIFY COLUMN execution_status_id SMALLINT UNSIGNED NOT NULL,
    ADD KEY idx_job_assignments_execution_status (
        execution_status_id, confirmation_deadline, id
    ),
    ADD CONSTRAINT fk_job_assignments_execution_status
        FOREIGN KEY (execution_status_id)
        REFERENCES job_execution_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT;
