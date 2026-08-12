CREATE TABLE schema_migrations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    version VARCHAR(20) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    checksum CHAR(64) NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_schema_migrations_version (version),
    UNIQUE KEY uq_schema_migrations_filename (filename)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
