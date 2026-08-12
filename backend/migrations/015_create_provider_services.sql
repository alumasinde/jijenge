CREATE TABLE provider_services (
    provider_id BIGINT UNSIGNED NOT NULL,
    service_id INT UNSIGNED NOT NULL,
    years_experience SMALLINT UNSIGNED NULL,
    minimum_price DECIMAL(12,2) NULL,
    maximum_price DECIMAL(12,2) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (provider_id, service_id),
    KEY idx_provider_services_service_active (service_id, is_active),
    KEY idx_provider_services_provider_active (provider_id, is_active),
    KEY idx_provider_services_price_range (service_id, minimum_price, maximum_price),

    CONSTRAINT fk_provider_services_provider
        FOREIGN KEY (provider_id)
        REFERENCES provider_profiles (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_provider_services_service
        FOREIGN KEY (service_id)
        REFERENCES services (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_provider_services_min_price
        CHECK (minimum_price IS NULL OR minimum_price >= 0),

    CONSTRAINT chk_provider_services_max_price
        CHECK (maximum_price IS NULL OR maximum_price >= 0),

    CONSTRAINT chk_provider_services_price_order
        CHECK (
            minimum_price IS NULL
            OR maximum_price IS NULL
            OR maximum_price >= minimum_price
        )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
