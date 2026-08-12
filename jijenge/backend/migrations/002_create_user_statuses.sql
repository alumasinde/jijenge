CREATE TABLE user_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_user_statuses_code (code),
    UNIQUE KEY uq_user_statuses_name (name),
    KEY idx_user_statuses_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO user_statuses (code, name, description, sort_order) VALUES
('ACTIVE', 'Active', 'User can access the platform.', 10),
('PENDING', 'Pending', 'User registration or verification is pending.', 20),
('SUSPENDED', 'Suspended', 'User access has been temporarily suspended.', 30),
('DISABLED', 'Disabled', 'User account has been disabled.', 40);
