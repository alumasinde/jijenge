CREATE TABLE trust_report_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NULL,
    applies_to VARCHAR(60) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,

    PRIMARY KEY (id),
    UNIQUE KEY uq_trust_report_types_code (code),
    UNIQUE KEY uq_trust_report_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO trust_report_types
    (code, name, description, applies_to)
VALUES
('FRAUD', 'Fraud', 'Suspected fraudulent activity.', 'USER'),
('HARASSMENT', 'Harassment', 'Harassment or abusive conduct.', 'USER'),
('SAFETY', 'Safety Concern', 'A safety-related concern.', 'USER_JOB'),
('FAKE_PROFILE', 'Fake Profile', 'Suspected fake or misleading profile.', 'USER'),
('PAYMENT_ABUSE', 'Payment Abuse', 'Payment-related abuse or manipulation.', 'USER_JOB'),
('REVIEW_ABUSE', 'Review Abuse', 'Manipulated or abusive review activity.', 'REVIEW');

CREATE TABLE trust_report_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,

    PRIMARY KEY (id),
    UNIQUE KEY uq_trust_report_statuses_code (code),
    UNIQUE KEY uq_trust_report_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO trust_report_statuses (code, name, is_terminal) VALUES
('OPEN', 'Open', 0),
('UNDER_REVIEW', 'Under Review', 0),
('RESOLVED', 'Resolved', 1),
('DISMISSED', 'Dismissed', 1);

CREATE TABLE trust_reports (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    reporter_user_id BIGINT UNSIGNED NOT NULL,
    report_type_id SMALLINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    reported_user_id BIGINT UNSIGNED NULL,
    job_id BIGINT UNSIGNED NULL,
    review_id BIGINT UNSIGNED NULL,
    description VARCHAR(3000) NOT NULL,
    evidence_json JSON NULL,
    assigned_to_user_id BIGINT UNSIGNED NULL,
    resolution_notes VARCHAR(3000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_trust_reports_public_id (public_id),
    KEY idx_trust_reports_status_created (
        status_id, created_at, id
    ),
    KEY idx_trust_reports_reporter_created (
        reporter_user_id, created_at
    ),
    KEY idx_trust_reports_reported_user_status (
        reported_user_id, status_id, created_at
    ),
    KEY idx_trust_reports_job_status (
        job_id, status_id, created_at
    ),
    KEY idx_trust_reports_review_status (
        review_id, status_id, created_at
    ),

    CONSTRAINT fk_trust_reports_reporter
        FOREIGN KEY (reporter_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_trust_reports_type
        FOREIGN KEY (report_type_id)
        REFERENCES trust_report_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_trust_reports_status
        FOREIGN KEY (status_id)
        REFERENCES trust_report_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_trust_reports_reported_user
        FOREIGN KEY (reported_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_trust_reports_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_trust_reports_review
        FOREIGN KEY (review_id)
        REFERENCES reviews (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_trust_reports_assignee
        FOREIGN KEY (assigned_to_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
