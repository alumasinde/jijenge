INSERT INTO ledger_entry_types (code,name,is_active)
VALUES ('CUSTOMER_PAYMENT','Customer Payment',1),('PLATFORM_COMMISSION','Platform Commission',1),('PROVIDER_EARNING','Provider Earning',1),('REFUND','Refund',1),('PAYOUT','Provider Payout',1),('PAYOUT_REVERSAL','Payout Reversal',1),('REFUND_REVERSAL','Refund Reversal',1)
ON DUPLICATE KEY UPDATE name=VALUES(name),is_active=1;
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
    CONSTRAINT fk_financial_ledger_type FOREIGN KEY (entry_type_id) REFERENCES ledger_entry_types(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_financial_ledger_payment FOREIGN KEY (payment_transaction_id) REFERENCES payment_transactions(id) ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_refund FOREIGN KEY (refund_id) REFERENCES refunds(id) ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_settlement FOREIGN KEY (settlement_id) REFERENCES provider_settlements(id) ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_earning FOREIGN KEY (provider_earning_id) REFERENCES provider_earnings(id) ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_financial_ledger_assignment FOREIGN KEY (assignment_id) REFERENCES job_assignments(id) ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
