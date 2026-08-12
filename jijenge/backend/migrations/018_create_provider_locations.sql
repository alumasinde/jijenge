CREATE TABLE provider_locations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider_id BIGINT UNSIGNED NOT NULL,
    location_id BIGINT UNSIGNED NULL,
    location_point POINT SRID 4326 NOT NULL,
    address_line VARCHAR(500) NULL,
    accuracy_meters DECIMAL(10,2) NULL,
    is_primary TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_provider_locations_provider_active (provider_id, is_active),
    KEY idx_provider_locations_primary (provider_id, is_primary),
    KEY idx_provider_locations_location (location_id),
    SPATIAL KEY spx_provider_locations_point (location_point),

    CONSTRAINT fk_provider_locations_provider
        FOREIGN KEY (provider_id)
        REFERENCES provider_profiles (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_provider_locations_location
        FOREIGN KEY (location_id)
        REFERENCES locations (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT chk_provider_locations_accuracy
        CHECK (accuracy_meters IS NULL OR accuracy_meters >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
