CREATE TABLE countries (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code CHAR(2) NOT NULL,
    name VARCHAR(120) NOT NULL,
    phone_code VARCHAR(10) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_countries_code (code),
    UNIQUE KEY uq_countries_name (name),
    KEY idx_countries_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE counties (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    country_id SMALLINT UNSIGNED NOT NULL,
    code VARCHAR(20) NULL,
    name VARCHAR(120) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_counties_country_name (country_id, name),
    UNIQUE KEY uq_counties_country_code (country_id, code),
    KEY idx_counties_country_active (country_id, is_active),

    CONSTRAINT fk_counties_country
        FOREIGN KEY (country_id)
        REFERENCES countries (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sub_counties (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    county_id INT UNSIGNED NOT NULL,
    code VARCHAR(30) NULL,
    name VARCHAR(120) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_sub_counties_county_name (county_id, name),
    UNIQUE KEY uq_sub_counties_county_code (county_id, code),
    KEY idx_sub_counties_county_active (county_id, is_active),

    CONSTRAINT fk_sub_counties_county
        FOREIGN KEY (county_id)
        REFERENCES counties (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO countries (code, name, phone_code)
VALUES ('KE', 'Kenya', '+254');
