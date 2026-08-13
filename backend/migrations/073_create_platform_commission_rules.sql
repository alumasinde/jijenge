CREATE TABLE IF NOT EXISTS commission_rule_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(40) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_commission_rule_types_code (code),
    UNIQUE KEY uq_commission_rule_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO commission_rule_types (code, name) VALUES
('PERCENTAGE', 'Percentage'),
('FIXED', 'Fixed')
ON DUPLICATE KEY UPDATE
    name = VALUES(name);

CREATE TABLE IF NOT EXISTS commission_rules (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    name VARCHAR(150) NOT NULL,
    rule_type_id SMALLINT UNSIGNED NOT NULL,
    percentage_rate DECIMAL(7,4) NULL,
    fixed_amount DECIMAL(14,2) NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    min_fee DECIMAL(14,2) NULL,
    max_fee DECIMAL(14,2) NULL,
    service_category_id INT UNSIGNED NULL,
    provider_id BIGINT UNSIGNED NULL,
    starts_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ends_at TIMESTAMP NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_commission_rules_public_id (public_id),
    KEY idx_commission_rules_lookup (
        is_active, service_category_id, provider_id, starts_at, ends_at, id
    ),
    KEY idx_commission_rules_type (rule_type_id),
    KEY idx_commission_rules_provider (provider_id, is_active, starts_at),
    CONSTRAINT fk_commission_rules_type
        FOREIGN KEY (rule_type_id) REFERENCES commission_rule_types(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_commission_rules_category
        FOREIGN KEY (service_category_id) REFERENCES service_categories(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_commission_rules_provider
        FOREIGN KEY (provider_id) REFERENCES provider_profiles(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT chk_commission_rule_values CHECK (
        (percentage_rate IS NOT NULL AND fixed_amount IS NULL)
        OR (percentage_rate IS NULL AND fixed_amount IS NOT NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO commission_rules
    (
        public_id, name, rule_type_id, percentage_rate,
        currency_code, is_active
    )
SELECT
    UUID(), 'Default Platform Commission', crt.id, 10.0000,
    'KES', 1
FROM commission_rule_types crt
WHERE crt.code = 'PERCENTAGE'
  AND NOT EXISTS (
      SELECT 1 FROM commission_rules
      WHERE name = 'Default Platform Commission'
  );
