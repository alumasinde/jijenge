ALTER TABLE settlements
    ADD COLUMN evidence_reference VARCHAR(255) NULL AFTER currency,
    ADD COLUMN confirmation_note VARCHAR(1000) NULL AFTER confirmed_at,
    ADD COLUMN dispute_reason VARCHAR(2000) NULL AFTER confirmation_note,
    ADD KEY idx_settlement_assignment_status(assignment_id,status),
    ADD CONSTRAINT chk_settlement_evidence CHECK (
        status = 'pending' OR evidence_reference IS NOT NULL
    );
