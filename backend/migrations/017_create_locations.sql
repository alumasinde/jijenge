CREATE TABLE locations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    country_id SMALLINT UNSIGNED NOT NULL,
    county_id INT UNSIGNED NULL,
    sub_county_id INT UNSIGNED NULL,
    name VARCHAR(180) NOT NULL,
    address_line VARCHAR(500) NULL,
    postal_code VARCHAR(30) NULL,
    latitude DECIMAL(10,7) NULL,
    longitude DECIMAL(10,7) NULL,
    location_point POINT SRID 4326 NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_locations_country (country_id),
    KEY idx_locations_county (county_id),
    KEY idx_locations_sub_county (sub_county_id),
    KEY idx_locations_active_name (is_active, name),
    SPATIAL KEY spx_locations_point (location_point),

    CONSTRAINT fk_locations_country
        FOREIGN KEY (country_id)
        REFERENCES countries (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_locations_county
        FOREIGN KEY (county_id)
        REFERENCES counties (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_locations_sub_county
        FOREIGN KEY (sub_county_id)
        REFERENCES sub_counties (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT chk_locations_latitude
        CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90)),

    CONSTRAINT chk_locations_longitude
        CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
