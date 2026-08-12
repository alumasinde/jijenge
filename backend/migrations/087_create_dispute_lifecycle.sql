-- Extend the dispute model from 072 rather than recreating dispute_statuses.

INSERT INTO dispute_statuses (code, name, is_terminal, is_active, sort_order)
VALUES
    ('RESOLVED_PROVIDER', 'Resolved - Provider Favored', 1, 1, 60),
    ('RESOLVED_CUSTOMER', 'Resolved - Customer Favored', 1, 1, 70),
    ('PARTIALLY_RESOLVED', 'Partially Resolved', 1, 1, 80)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    is_terminal = VALUES(is_terminal),
    is_active = 1,
    sort_order = VALUES(sort_order);

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
