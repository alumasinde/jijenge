CREATE TABLE dispute_evidence_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dispute_evidence_types_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO dispute_evidence_types (code,name) VALUES ('PHOTO','Photo'),('VIDEO','Video'),('DOCUMENT','Document'),('MESSAGE','Message'),('LOCATION','Location'),('NOTE','Note');
CREATE TABLE dispute_evidence (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    dispute_id BIGINT UNSIGNED NOT NULL,
    evidence_type_id SMALLINT UNSIGNED NOT NULL,
    submitted_by_user_id BIGINT UNSIGNED NOT NULL,
    storage_key VARCHAR(1000) NULL,
    content_text TEXT NULL,
    latitude DECIMAL(10,7) NULL,
    longitude DECIMAL(10,7) NULL,
    metadata_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_dispute_evidence_dispute (dispute_id,created_at,id),
    KEY idx_dispute_evidence_submitter (submitted_by_user_id,created_at),
    CONSTRAINT fk_dispute_evidence_dispute FOREIGN KEY (dispute_id) REFERENCES disputes(id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_dispute_evidence_type FOREIGN KEY (evidence_type_id) REFERENCES dispute_evidence_types(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_dispute_evidence_submitter FOREIGN KEY (submitted_by_user_id) REFERENCES users(id) ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
