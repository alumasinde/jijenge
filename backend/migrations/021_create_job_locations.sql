CREATE TABLE job_locations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_id BIGINT UNSIGNED NOT NULL,
    location_id BIGINT UNSIGNED NULL,
    location_point POINT SRID 4326 NOT NULL,
    address_line VARCHAR(500) NULL,
    location_notes VARCHAR(1000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_job_locations_job (job_id),
    KEY idx_job_locations_location (location_id),
    SPATIAL KEY spx_job_locations_point (location_point),

    CONSTRAINT fk_job_locations_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_job_locations_location
        FOREIGN KEY (location_id)
        REFERENCES locations (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
