CREATE TABLE ledger_entry_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(70) NOT NULL,
    name VARCHAR(140) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_ledger_entry_types_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO ledger_entry_types (code,name) VALUES
('CUSTOMER_PAYMENT','Customer Payment'),
('PLATFORM_COMMISSION','Platform Commission'),
('PROVIDER_EARNING','Provider Earning'),
('REFUND','Refund'),
('PAYOUT','Provider Payout'),
('PAYOUT_REVERSAL','Payout Reversal'),
('REFUND_REVERSAL','Refund Reversal');

CREATE TABLE financial_ledger_entries (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    entry_type_id SMALLINT UNSIGNED NOT NULL,
    payment_transaction_id BIGINT UNSIGNED NULL,
    refund_id BIGINT UNSIGNED NULL,
    settlement_id BIGINT UNSIGNED NULL,
    provider_earning_id BIGINT UNSIGNED NULL,
    job_id BIGINT UNSIGNED NULL,
    assignment_id BIGINT UNSIGNED NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    direction VARCHAR(20) NOT NULL,
    reference VARCHAR(255) NULL,
    description VARCHAR(1000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_financial_ledger_entries_public_id (public_id),
    KEY idx_financial_ledger_payment (payment_transaction_id,created_at),
    KEY idx_financial_ledger_refund (refund_id,created_at),
    KEY idx_financial_ledger_settlement (settlement_id,created_at),
    KEY idx_financial_ledger_provider_earning (provider_earning_id,created_at),
    KEY idx_financial_ledger_job (job_id,created_at),
    CONSTRAINT fk_financial_ledger_type
        FOREIGN KEY (entry_type_id) REFERENCES ledger_entry_types(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_financial_ledger_payment
        FOREIGN KEY (payment_transaction_id) REFERENCES payment_transactions(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_refund
        FOREIGN KEY (refund_id) REFERENCES refunds(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_settlement
        FOREIGN KEY (settlement_id) REFERENCES provider_settlements(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_earning
        FOREIGN KEY (provider_earning_id) REFERENCES provider_earnings(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_job
        FOREIGN KEY (job_id) REFERENCES jobs(id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_assignment
        FOREIGN KEY (assignment_id) REFERENCES job_assignments(id)
        ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
