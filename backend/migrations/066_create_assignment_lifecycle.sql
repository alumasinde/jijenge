CREATE TABLE assignment_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_assignment_statuses_code (code),
    UNIQUE KEY uq_assignment_statuses_name (name),
    KEY idx_assignment_statuses_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO assignment_statuses
    (code, name, is_terminal, is_success, sort_order)
VALUES
('PENDING_PROVIDER_CONFIRMATION', 'Pending Provider Confirmation', 0, 0, 10),
('CONFIRMED', 'Confirmed', 0, 1, 20),
('PROVIDER_DECLINED', 'Provider Declined', 1, 0, 30),
('CANCELLED', 'Cancelled', 1, 0, 40),
('IN_PROGRESS', 'In Progress', 0, 1, 50),
('COMPLETED', 'Completed', 1, 1, 60),
('FAILED', 'Failed', 1, 0, 70);

ALTER TABLE job_assignments
    ADD COLUMN status_id SMALLINT UNSIGNED NULL AFTER application_id,
    ADD COLUMN confirmation_deadline TIMESTAMP NULL AFTER assigned_at,
    ADD COLUMN confirmed_at TIMESTAMP NULL AFTER confirmation_deadline,
    ADD COLUMN declined_at TIMESTAMP NULL AFTER confirmed_at,
    ADD COLUMN decline_reason VARCHAR(1000) NULL AFTER declined_at;

UPDATE job_assignments ja
INNER JOIN assignment_statuses ass
    ON ass.code = 'CONFIRMED'
SET ja.status_id = ass.id,
    ja.confirmed_at = ja.assigned_at;

ALTER TABLE job_assignments
    MODIFY COLUMN status_id SMALLINT UNSIGNED NOT NULL;

ALTER TABLE job_assignments
    ADD KEY idx_job_assignments_status_deadline (
        status_id, confirmation_deadline, id
    ),
    ADD KEY idx_job_assignments_provider_status (
        provider_id, status_id, cancelled_at, completed_at
    ),
    ADD CONSTRAINT fk_job_assignments_status
        FOREIGN KEY (status_id)
        REFERENCES assignment_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT;
