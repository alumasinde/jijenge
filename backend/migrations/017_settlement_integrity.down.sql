ALTER TABLE settlements
    DROP CONSTRAINT chk_settlement_evidence,
    DROP INDEX idx_settlement_assignment_status,
    DROP COLUMN dispute_reason,
    DROP COLUMN confirmation_note,
    DROP COLUMN evidence_reference;
