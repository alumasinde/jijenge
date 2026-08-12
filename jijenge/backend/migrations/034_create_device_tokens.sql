CREATE TABLE device_tokens (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    platform VARCHAR(30) NOT NULL,
    token VARCHAR(500) NOT NULL,
    device_name VARCHAR(180) NULL,
    app_version VARCHAR(50) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_seen_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_device_tokens_token (token),
    KEY idx_device_tokens_user_active (
        user_id, is_active, updated_at
    ),

    CONSTRAINT fk_device_tokens_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
