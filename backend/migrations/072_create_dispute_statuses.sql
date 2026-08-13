CREATE TABLE dispute_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dispute_statuses_code (code),
    UNIQUE KEY uq_dispute_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO dispute_statuses (code,name,is_terminal,sort_order) VALUES
('OPEN','Open',0,10),('UNDER_REVIEW','Under Review',0,20),('RESOLVED','Resolved',1,30),('REJECTED','Rejected',1,40),('CANCELLED','Cancelled',1,50);

CREATE TABLE dispute_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dispute_types_code (code),
    UNIQUE KEY uq_dispute_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO dispute_types (code,name,description) VALUES
('QUALITY','Quality','Work quality is disputed.'),('NO_SHOW','No Show','Provider or customer did not attend.'),('DAMAGE','Damage','Property damage is disputed.'),('PRICE','Price','Price or charges are disputed.'),('SAFETY','Safety','A safety issue is reported.'),('OTHER','Other','Another job issue is disputed.');

CREATE TABLE job_disputes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    assignment_id BIGINT UNSIGNED NOT NULL,
    opened_by_user_id BIGINT UNSIGNED NOT NULL,
    dispute_type_id SMALLINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    description VARCHAR(4000) NOT NULL,
    resolution_notes VARCHAR(4000) NULL,
    resolved_by_user_id BIGINT UNSIGNED NULL,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_job_disputes_assignment_status (assignment_id,status_id,created_at),
    KEY idx_job_disputes_status_created (status_id,created_at),
    KEY idx_job_disputes_opener_created (opened_by_user_id,created_at),
    CONSTRAINT fk_job_disputes_assignment FOREIGN KEY (assignment_id) REFERENCES job_assignments(id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_job_disputes_opener FOREIGN KEY (opened_by_user_id) REFERENCES users(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_job_disputes_type FOREIGN KEY (dispute_type_id) REFERENCES dispute_types(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_job_disputes_status FOREIGN KEY (status_id) REFERENCES dispute_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_job_disputes_resolver FOREIGN KEY (resolved_by_user_id) REFERENCES users(id) ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
