CREATE TABLE settlement_hold_rules (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    name VARCHAR(150) NOT NULL,
    hold_hours INT UNSIGNED NOT NULL DEFAULT 24,
    service_category_id BIGINT UNSIGNED NULL,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_settlement_hold_rules_public_id (public_id),
    KEY idx_settlement_hold_rules_lookup (
        is_active,service_category_id,is_default,id
    ),
    CONSTRAINT fk_settlement_hold_rules_category
        FOREIGN KEY (service_category_id) REFERENCES service_categories(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO settlement_hold_rules
    (public_id,name,hold_hours,is_default,is_active)
SELECT UUID(),'Default Settlement Hold',24,1,1
WHERE NOT EXISTS (
    SELECT 1 FROM settlement_hold_rules WHERE is_default=1 AND is_active=1
);
