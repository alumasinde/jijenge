CREATE TABLE platform_revenue_entry_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_platform_revenue_entry_types_code (code),
    UNIQUE KEY uq_platform_revenue_entry_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO platform_revenue_entry_types (code,name) VALUES ('JOB_COMMISSION','Job Commission'),('PAYMENT_PROCESSING','Payment Processing'),('ADJUSTMENT','Adjustment'),('REVERSAL','Reversal');
CREATE TABLE platform_revenue_entries (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    assignment_id BIGINT UNSIGNED NOT NULL,
    job_id BIGINT UNSIGNED NOT NULL,
    entry_type_id SMALLINT UNSIGNED NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'KES',
    financial_breakdown_id BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_platform_revenue_entries_public_id (public_id),
    UNIQUE KEY uq_platform_revenue_entries_assignment_type (assignment_id,entry_type_id),
    KEY idx_platform_revenue_entries_job_created (job_id,created_at,id),
    KEY idx_platform_revenue_entries_breakdown (financial_breakdown_id),
    CONSTRAINT fk_platform_revenue_entries_assignment FOREIGN KEY (assignment_id) REFERENCES job_assignments(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_platform_revenue_entries_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_platform_revenue_entries_type FOREIGN KEY (entry_type_id) REFERENCES platform_revenue_entry_types(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_platform_revenue_entries_breakdown FOREIGN KEY (financial_breakdown_id) REFERENCES job_financial_breakdowns(id) ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
