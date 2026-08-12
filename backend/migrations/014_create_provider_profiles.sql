CREATE TABLE provider_profiles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    provider_status_id SMALLINT UNSIGNED NOT NULL,
    business_name VARCHAR(180) NULL,
    professional_title VARCHAR(180) NULL,
    bio TEXT NULL,
    years_experience SMALLINT UNSIGNED NULL,
    is_verified TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_profiles_user_id (user_id),
    KEY idx_provider_profiles_status (provider_status_id),
    KEY idx_provider_profiles_active_verified (provider_status_id, is_verified),

    CONSTRAINT fk_provider_profiles_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_provider_profiles_status
        FOREIGN KEY (provider_status_id)
        REFERENCES provider_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
