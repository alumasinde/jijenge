CREATE TABLE provider_matching_preferences (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider_id BIGINT UNSIGNED NOT NULL,
    max_distance_km DECIMAL(8,2) NOT NULL DEFAULT 25.00,
    accepts_new_jobs TINYINT(1) NOT NULL DEFAULT 1,
    auto_match_enabled TINYINT(1) NOT NULL DEFAULT 1,
    minimum_notice_minutes INT UNSIGNED NOT NULL DEFAULT 60,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_matching_preferences_provider (provider_id),
    KEY idx_provider_matching_preferences_discovery (
        accepts_new_jobs, auto_match_enabled, max_distance_km
    ),

    CONSTRAINT fk_provider_matching_preferences_provider
        FOREIGN KEY (provider_id)
        REFERENCES provider_profiles (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT chk_provider_matching_preferences_distance
        CHECK (max_distance_km > 0 AND max_distance_km <= 500),

    CONSTRAINT chk_provider_matching_preferences_notice
        CHECK (minimum_notice_minutes <= 10080)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
