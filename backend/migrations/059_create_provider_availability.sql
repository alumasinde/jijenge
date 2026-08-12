CREATE TABLE availability_rule_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_availability_rule_statuses_code (code),
    UNIQUE KEY uq_availability_rule_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO availability_rule_statuses (code, name) VALUES
('ACTIVE', 'Active'),
('INACTIVE', 'Inactive');

CREATE TABLE provider_availability_rules (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    day_of_week TINYINT UNSIGNED NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    effective_from DATE NULL,
    effective_to DATE NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_provider_availability_provider_day_status (
        provider_id, day_of_week, status_id, start_time
    ),
    KEY idx_provider_availability_effective (
        effective_from, effective_to, status_id
    ),

    CONSTRAINT fk_provider_availability_provider
        FOREIGN KEY (provider_id)
        REFERENCES provider_profiles (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_provider_availability_status
        FOREIGN KEY (status_id)
        REFERENCES availability_rule_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_provider_availability_day
        CHECK (day_of_week BETWEEN 1 AND 7),

    CONSTRAINT chk_provider_availability_time
        CHECK (start_time < end_time),

    CONSTRAINT chk_provider_availability_dates
        CHECK (
            effective_to IS NULL
            OR effective_from IS NULL
            OR effective_to >= effective_from
        )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE provider_availability_exceptions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider_id BIGINT UNSIGNED NOT NULL,
    exception_date DATE NOT NULL,
    is_available TINYINT(1) NOT NULL DEFAULT 0,
    start_time TIME NULL,
    end_time TIME NULL,
    reason VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_availability_exception_date (
        provider_id, exception_date
    ),
    KEY idx_provider_availability_exception_date (
        exception_date, provider_id
    ),

    CONSTRAINT fk_provider_availability_exception_provider
        FOREIGN KEY (provider_id)
        REFERENCES provider_profiles (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT chk_provider_availability_exception_time
        CHECK (
            (is_available = 0 AND start_time IS NULL AND end_time IS NULL)
            OR
            (is_available = 1 AND start_time IS NOT NULL
             AND end_time IS NOT NULL AND start_time < end_time)
        )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
