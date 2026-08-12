CREATE TABLE dispute_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dispute_statuses_code (code),
    UNIQUE KEY uq_dispute_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO dispute_statuses (code,name,is_terminal) VALUES
('OPEN','Open',0),
('UNDER_REVIEW','Under Review',0),
('RESOLVED_PROVIDER','Resolved - Provider Favored',1),
('RESOLVED_CUSTOMER','Resolved - Customer Favored',1),
('PARTIALLY_RESOLVED','Partially Resolved',1),
('REJECTED','Rejected',1),
('CANCELLED','Cancelled',1);

CREATE TABLE dispute_reasons (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(70) NOT NULL,
    name VARCHAR(140) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dispute_reasons_code (code),
    UNIQUE KEY uq_dispute_reasons_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO dispute_reasons (code,name) VALUES
('QUALITY','Quality Issue'),
('INCOMPLETE','Work Incomplete'),
('DAMAGE','Property Damage'),
('NO_SHOW','Provider No Show'),
('WRONG_SERVICE','Wrong Service'),
('OVERCHARGE','Payment/Price Issue'),
('SAFETY','Safety Concern'),
('OTHER','Other');

CREATE TABLE disputes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    job_id BIGINT UNSIGNED NOT NULL,
    assignment_id BIGINT UNSIGNED NOT NULL,
    opened_by_user_id BIGINT UNSIGNED NOT NULL,
    reason_id SMALLINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    description TEXT NOT NULL,
    disputed_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    resolved_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    opened_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    resolved_by_user_id BIGINT UNSIGNED NULL,
    resolution_notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_disputes_public_id (public_id),
    KEY idx_disputes_job_status (job_id,status_id,created_at),
    KEY idx_disputes_assignment_status (assignment_id,status_id,created_at),
    KEY idx_disputes_opener (opened_by_user_id,status_id,created_at),
    CONSTRAINT fk_disputes_job
        FOREIGN KEY (job_id) REFERENCES jobs(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_disputes_assignment
        FOREIGN KEY (assignment_id) REFERENCES job_assignments(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_disputes_opener
        FOREIGN KEY (opened_by_user_id) REFERENCES users(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_disputes_reason
        FOREIGN KEY (reason_id) REFERENCES dispute_reasons(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_disputes_status
        FOREIGN KEY (status_id) REFERENCES dispute_statuses(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_disputes_resolver
        FOREIGN KEY (resolved_by_user_id) REFERENCES users(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
