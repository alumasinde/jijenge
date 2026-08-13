INSERT INTO notification_types (code, name, description)
VALUES
('ASSIGNMENT_CONFIRMATION_REQUIRED','Assignment Confirmation Required','A provider must confirm a new job assignment.'),
('ASSIGNMENT_CONFIRMED','Assignment Confirmed','A provider confirmed a job assignment.'),
('ASSIGNMENT_DECLINED','Assignment Declined','A provider declined a job assignment.');

CREATE TABLE assignment_dispatch_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_assignment_dispatch_statuses_code (code),
    UNIQUE KEY uq_assignment_dispatch_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO assignment_dispatch_statuses (code, name) VALUES
('PENDING','Pending'),('SENT','Sent'),('EXPIRED','Expired'),('FAILED','Failed');

CREATE TABLE assignment_dispatches (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    assignment_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    attempt_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    last_error VARCHAR(2000) NULL,
    sent_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_assignment_dispatches_assignment (assignment_id),
    KEY idx_assignment_dispatches_status_expires (status_id, expires_at, id),
    CONSTRAINT fk_assignment_dispatches_assignment FOREIGN KEY (assignment_id) REFERENCES job_assignments(id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_assignment_dispatches_status FOREIGN KEY (status_id) REFERENCES assignment_dispatch_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
