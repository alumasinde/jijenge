CREATE TABLE financial_account_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,

    PRIMARY KEY (id),
    UNIQUE KEY uq_financial_account_types_code (code),
    UNIQUE KEY uq_financial_account_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO financial_account_types (code, name) VALUES
('CUSTOMER_PAYABLE', 'Customer Payable'),
('PROVIDER_EARNINGS', 'Provider Earnings'),
('PLATFORM_REVENUE', 'Platform Revenue'),
('PLATFORM_HOLDING', 'Platform Holding');

CREATE TABLE financial_accounts (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    owner_user_id BIGINT UNSIGNED NULL,
    account_type_id SMALLINT UNSIGNED NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    account_name VARCHAR(180) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_financial_accounts_public_id (public_id),
    KEY idx_financial_accounts_owner_type (
        owner_user_id, account_type_id, is_active
    ),
    KEY idx_financial_accounts_type_currency (
        account_type_id, currency_code, is_active
    ),

    CONSTRAINT fk_financial_accounts_owner
        FOREIGN KEY (owner_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_financial_accounts_type
        FOREIGN KEY (account_type_id)
        REFERENCES financial_account_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_financial_accounts_currency
        CHECK (CHAR_LENGTH(currency_code) = 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
