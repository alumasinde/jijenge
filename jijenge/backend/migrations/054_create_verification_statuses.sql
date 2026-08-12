CREATE TABLE verification_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_verification_statuses_code (code),
    UNIQUE KEY uq_verification_statuses_name (name),
    KEY idx_verification_statuses_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO verification_statuses
    (code, name, description, is_terminal, is_success, sort_order)
VALUES
('PENDING', 'Pending', 'Verification has not yet been reviewed.', 0, 0, 10),
('UNDER_REVIEW', 'Under Review', 'Verification is being reviewed.', 0, 0, 20),
('VERIFIED', 'Verified', 'Verification was approved.', 1, 1, 30),
('REJECTED', 'Rejected', 'Verification was rejected.', 1, 0, 40),
('EXPIRED', 'Expired', 'Verification has expired.', 1, 0, 50),
('REVOKED', 'Revoked', 'Verification was revoked.', 1, 0, 60);
