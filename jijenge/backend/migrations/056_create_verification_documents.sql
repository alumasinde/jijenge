CREATE TABLE verification_document_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,

    PRIMARY KEY (id),
    UNIQUE KEY uq_verification_document_types_code (code),
    UNIQUE KEY uq_verification_document_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO verification_document_types
    (code, name, description, sort_order)
VALUES
('NATIONAL_ID', 'National ID', 'Identity document.', 10),
('PASSPORT', 'Passport', 'Passport document.', 20),
('LICENSE', 'Professional License', 'Professional licence or registration.', 30),
('CERTIFICATE', 'Certificate', 'Professional qualification certificate.', 40),
('BUSINESS_DOCUMENT', 'Business Document', 'Business registration or supporting document.', 50);

CREATE TABLE verification_documents (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    verification_request_id BIGINT UNSIGNED NOT NULL,
    document_type_id SMALLINT UNSIGNED NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255) NULL,
    mime_type VARCHAR(120) NOT NULL,
    file_size_bytes BIGINT UNSIGNED NOT NULL,
    sha256_hash CHAR(64) NULL,
    document_number_masked VARCHAR(120) NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    reviewer_notes VARCHAR(1000) NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_verification_documents_public_id (public_id),
    KEY idx_verification_documents_request_status (
        verification_request_id, status_id, uploaded_at
    ),
    KEY idx_verification_documents_hash (sha256_hash),

    CONSTRAINT fk_verification_documents_request
        FOREIGN KEY (verification_request_id)
        REFERENCES verification_requests (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_verification_documents_type
        FOREIGN KEY (document_type_id)
        REFERENCES verification_document_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_verification_documents_status
        FOREIGN KEY (status_id)
        REFERENCES verification_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_verification_documents_size
        CHECK (file_size_bytes > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
