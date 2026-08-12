-- Extend the provider earnings model created in 045.
-- Keep the original columns for backwards compatibility with older services,
-- while adding the assignment/financial-breakdown model used by the current API.

ALTER TABLE provider_earning_statuses
    ADD COLUMN IF NOT EXISTS is_active TINYINT(1) NOT NULL DEFAULT 1 AFTER is_terminal;

INSERT INTO provider_earning_statuses (code, name, is_terminal, is_active)
VALUES
    ('ON_HOLD', 'On Hold', 0, 1)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    is_terminal = VALUES(is_terminal),
    is_active = 1;

ALTER TABLE provider_earnings
    ADD COLUMN IF NOT EXISTS provider_id BIGINT UNSIGNED NULL AFTER provider_user_id,
    ADD COLUMN IF NOT EXISTS assignment_id BIGINT UNSIGNED NULL AFTER job_id,
    ADD COLUMN IF NOT EXISTS financial_breakdown_id BIGINT UNSIGNED NULL AFTER assignment_id,
    ADD COLUMN IF NOT EXISTS processing_fee_amount DECIMAL(14,2) NOT NULL DEFAULT 0 AFTER platform_fee_amount;

-- Current services identify earnings by provider profile and assignment.
UPDATE provider_earnings pe
INNER JOIN job_assignments ja ON ja.id = pe.assignment_id
SET pe.provider_id = ja.provider_id
WHERE pe.provider_id IS NULL
  AND pe.assignment_id IS NOT NULL;

UPDATE provider_earnings pe
INNER JOIN job_assignments ja ON ja.job_id = pe.job_id
SET pe.assignment_id = ja.id,
    pe.provider_id = ja.provider_id
WHERE pe.assignment_id IS NULL;

ALTER TABLE provider_earnings
    MODIFY COLUMN provider_user_id BIGINT UNSIGNED NULL,
    MODIFY COLUMN job_id BIGINT UNSIGNED NULL,
    MODIFY COLUMN adjustment_amount DECIMAL(14,2) NOT NULL DEFAULT 0;

ALTER TABLE provider_earnings
    ADD KEY idx_provider_earnings_provider_profile (provider_id, status_id, created_at),
    ADD KEY idx_provider_earnings_assignment (assignment_id, status_id, created_at),
    ADD KEY idx_provider_earnings_breakdown (financial_breakdown_id);

ALTER TABLE provider_earnings
    ADD CONSTRAINT fk_provider_earnings_provider_profile
        FOREIGN KEY (provider_id) REFERENCES provider_profiles(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT fk_provider_earnings_assignment
        FOREIGN KEY (assignment_id) REFERENCES job_assignments(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT fk_provider_earnings_breakdown
        FOREIGN KEY (financial_breakdown_id) REFERENCES job_financial_breakdowns(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT;
