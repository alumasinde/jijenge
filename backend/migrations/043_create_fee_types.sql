CREATE TABLE fee_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NULL,
    calculation_type VARCHAR(40) NOT NULL,
    rate DECIMAL(8,4) NULL,
    fixed_amount DECIMAL(14,2) NULL,
    currency_code CHAR(3) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_fee_types_code (code),
    UNIQUE KEY uq_fee_types_name (name),
    KEY idx_fee_types_active (is_active),

    CONSTRAINT chk_fee_types_rate
        CHECK (rate IS NULL OR rate >= 0),
    CONSTRAINT chk_fee_types_fixed_amount
        CHECK (fixed_amount IS NULL OR fixed_amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO fee_types
    (code, name, description, calculation_type, rate, fixed_amount)
VALUES
    ('PLATFORM_COMMISSION', 'Platform Commission',
     'Platform commission charged on provider earnings.',
     'PERCENTAGE', 10.0000, NULL),
    ('PAYMENT_PROCESSING', 'Payment Processing',
     'Payment processing fee.',
     'FIXED', NULL, 0.00);
