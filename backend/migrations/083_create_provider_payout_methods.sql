CREATE TABLE provider_payout_method_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_payout_method_types_code (code),
    UNIQUE KEY uq_provider_payout_method_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO provider_payout_method_types (code,name) VALUES ('MPESA','M-Pesa'),('BANK','Bank Account'),('CASH','Cash');
CREATE TABLE provider_payout_methods (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    provider_id BIGINT UNSIGNED NOT NULL,
    method_type_id SMALLINT UNSIGNED NOT NULL,
    account_name VARCHAR(160) NOT NULL,
    account_reference VARCHAR(255) NOT NULL,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    is_verified TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_payout_methods_public_id (public_id),
    KEY idx_provider_payout_methods_provider (provider_id,is_active,is_default,id),
    KEY idx_provider_payout_methods_type (method_type_id,is_active),
    CONSTRAINT fk_provider_payout_methods_provider FOREIGN KEY (provider_id) REFERENCES provider_profiles(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_provider_payout_methods_type FOREIGN KEY (method_type_id) REFERENCES provider_payout_method_types(id) ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
