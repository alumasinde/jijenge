CREATE TABLE provider_service_areas (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider_id BIGINT UNSIGNED NOT NULL,
    center_point POINT SRID 4326 NOT NULL,
    radius_km DECIMAL(8,2) NOT NULL DEFAULT 10.00,
    name VARCHAR(180) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_provider_service_areas_provider_active (provider_id, is_active),
    KEY idx_provider_service_areas_active_radius (is_active, radius_km),
    SPATIAL KEY spx_provider_service_areas_point (center_point),

    CONSTRAINT fk_provider_service_areas_provider
        FOREIGN KEY (provider_id)
        REFERENCES provider_profiles (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT chk_provider_service_areas_radius
        CHECK (radius_km > 0 AND radius_km <= 500)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
