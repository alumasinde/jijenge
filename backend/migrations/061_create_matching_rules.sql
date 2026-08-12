CREATE TABLE matching_rule_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NULL,
    score_min DECIMAL(10,4) NOT NULL DEFAULT 0,
    score_max DECIMAL(10,4) NOT NULL DEFAULT 100,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_matching_rule_types_code (code),
    UNIQUE KEY uq_matching_rule_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO matching_rule_types
    (code, name, description)
VALUES
('DISTANCE', 'Distance', 'Score based on travel distance.'),
('RATING', 'Rating', 'Score based on published provider rating.'),
('VERIFICATION', 'Verification', 'Score based on verified provider status.'),
('AVAILABILITY', 'Availability', 'Score based on availability for the requested time.'),
('EXPERIENCE', 'Experience', 'Score based on provider service experience.');

CREATE TABLE matching_rules (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    rule_type_id SMALLINT UNSIGNED NOT NULL,
    weight DECIMAL(8,4) NOT NULL,
    configuration_json JSON NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_matching_rules_rule_type (rule_type_id),
    KEY idx_matching_rules_active (is_active),

    CONSTRAINT fk_matching_rules_type
        FOREIGN KEY (rule_type_id)
        REFERENCES matching_rule_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_matching_rules_weight
        CHECK (weight >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO matching_rules (rule_type_id, weight)
SELECT id, CASE code
    WHEN 'DISTANCE' THEN 35.0000
    WHEN 'RATING' THEN 25.0000
    WHEN 'VERIFICATION' THEN 15.0000
    WHEN 'AVAILABILITY' THEN 15.0000
    WHEN 'EXPERIENCE' THEN 10.0000
END
FROM matching_rule_types
WHERE is_active = 1;
