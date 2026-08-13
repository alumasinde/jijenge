CREATE TABLE system_settings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    setting_key VARCHAR(150) NOT NULL,
    value_json JSON NOT NULL,
    value_type VARCHAR(20) NOT NULL DEFAULT 'string',
    description VARCHAR(500) NULL,
    is_public TINYINT(1) NOT NULL DEFAULT 0,
    is_editable TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_system_settings_key (setting_key),
    KEY idx_system_settings_public (is_public),
    CONSTRAINT chk_system_settings_value_type CHECK (value_type IN ('string','integer','decimal','boolean','json'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO system_settings (setting_key,value_json,value_type,description,is_public,is_editable) VALUES
('default_currency',JSON_QUOTE('KES'),'string','Default platform currency code.',1,1),
('maintenance_mode',JSON_EXTRACT('false','$'),'boolean','Whether the platform is in maintenance mode.',1,1),
('matching_enabled',JSON_EXTRACT('true','$'),'boolean','Whether automated provider matching is enabled.',0,1),
('provider_application_expiry_minutes',JSON_EXTRACT('1440','$'),'integer','How long a provider application remains active before expiry.',0,1);
