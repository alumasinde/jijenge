CREATE TABLE payments (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    provider VARCHAR(64) NOT NULL,
    provider_ref VARCHAR(128) NOT NULL,
    provider_event_id VARCHAR(128) NULL,
    account_id BIGINT UNSIGNED NOT NULL,
    amount_cents BIGINT UNSIGNED NOT NULL,
    currency CHAR(3) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_payments_public_id (public_id),
    UNIQUE KEY uq_payments_provider_ref (provider,provider_ref),
    UNIQUE KEY uq_payments_provider_event (provider,provider_event_id),
    KEY idx_payments_account_status (account_id,status,created_at),
    CONSTRAINT fk_payments_account FOREIGN KEY (account_id) REFERENCES financial_accounts(id) ON DELETE RESTRICT,
    CONSTRAINT chk_payments_amount CHECK (amount_cents > 0),
    CONSTRAINT chk_payments_currency CHECK (currency REGEXP '^[A-Z]{3}$'),
    CONSTRAINT chk_payments_status CHECK (status IN ('pending','confirmed','failed','cancelled'))
) ENGINE=InnoDB;

CREATE TABLE payment_webhook_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider VARCHAR(64) NOT NULL,
    event_id VARCHAR(128) NOT NULL,
    payment_ref VARCHAR(128) NOT NULL,
    amount_cents BIGINT UNSIGNED NOT NULL,
    currency CHAR(3) NOT NULL,
    signature VARCHAR(512) NOT NULL,
    payload_hash BINARY(32) NOT NULL,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    processed_at TIMESTAMP(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_webhook_event (provider,event_id),
    KEY idx_payment_webhook_payment_ref (provider,payment_ref),
    CONSTRAINT chk_payment_webhook_amount CHECK (amount_cents > 0),
    CONSTRAINT chk_payment_webhook_currency CHECK (currency REGEXP '^[A-Z]{3}$')
) ENGINE=InnoDB;

CREATE TABLE payment_provider_accounts (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider VARCHAR(64) NOT NULL,
    account_id BIGINT UNSIGNED NOT NULL,
    provider_account_ref VARCHAR(128) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_account (provider,provider_account_ref),
    UNIQUE KEY uq_provider_account_owner (provider,account_id),
    CONSTRAINT fk_provider_accounts_financial FOREIGN KEY (account_id) REFERENCES financial_accounts(id) ON DELETE RESTRICT
) ENGINE=InnoDB;
