CREATE TABLE completion_evidence_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_completion_evidence_types_code (code),
    UNIQUE KEY uq_completion_evidence_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO completion_evidence_types (code,name) VALUES
('PHOTO','Photo'),('DOCUMENT','Document'),('SIGNATURE','Signature'),('NOTE','Note');

CREATE TABLE job_completion_evidence (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    assignment_id BIGINT UNSIGNED NOT NULL,
    evidence_type_id SMALLINT UNSIGNED NOT NULL,
    storage_key VARCHAR(1000) NULL,
    text_value VARCHAR(4000) NULL,
    mime_type VARCHAR(120) NULL,
    created_by_user_id BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_job_completion_evidence_assignment_created (assignment_id,created_at,id),
    CONSTRAINT fk_job_completion_evidence_assignment FOREIGN KEY (assignment_id) REFERENCES job_assignments(id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_job_completion_evidence_type FOREIGN KEY (evidence_type_id) REFERENCES completion_evidence_types(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_job_completion_evidence_creator FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_job_completion_evidence_value CHECK (storage_key IS NOT NULL OR text_value IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
