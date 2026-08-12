CREATE TABLE verification_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NULL,
    applies_to VARCHAR(50) NOT NULL,
    requires_document TINYINT(1) NOT NULL DEFAULT 1,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_verification_types_code (code),
    UNIQUE KEY uq_verification_types_name (name),
    KEY idx_verification_types_active_target (
        applies_to, is_active, sort_order
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO verification_types
    (code, name, description, applies_to, requires_document, sort_order)
VALUES
('IDENTITY', 'Identity Verification',
 'Verification of the provider identity.', 'PROVIDER', 1, 10),
('PROFESSIONAL', 'Professional Verification',
 'Verification of professional qualifications or credentials.', 'PROVIDER', 1, 20),
('BUSINESS', 'Business Verification',
 'Verification of a provider business where applicable.', 'PROVIDER', 1, 30),
('PHONE', 'Phone Verification',
 'Verification of an account phone number.', 'USER', 0, 40);

CREATE TABLE verification_requests (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    verification_type_id SMALLINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    submitted_at TIMESTAMP NULL,
    reviewed_at TIMESTAMP NULL,
    reviewed_by_user_id BIGINT UNSIGNED NULL,
    rejection_reason VARCHAR(1000) NULL,
    reviewer_notes VARCHAR(2000) NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_verification_requests_public_id (public_id),
    KEY idx_verification_requests_user_type_status (
        user_id, verification_type_id, status_id, created_at
    ),
    KEY idx_verification_requests_review_queue (
        status_id, submitted_at, id
    ),

    CONSTRAINT fk_verification_requests_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_verification_requests_type
        FOREIGN KEY (verification_type_id)
        REFERENCES verification_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_verification_requests_status
        FOREIGN KEY (status_id)
        REFERENCES verification_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_verification_requests_reviewer
        FOREIGN KEY (reviewed_by_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
