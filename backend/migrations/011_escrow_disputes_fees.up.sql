
ALTER TABLE escrow_payments
    ADD COLUMN platform_fee_cents BIGINT UNSIGNED NOT NULL DEFAULT 0 AFTER amount_cents,
    ADD COLUMN dispute_id BIGINT UNSIGNED NULL AFTER released_at,
    ADD KEY idx_escrow_dispute (dispute_id),
    ADD CONSTRAINT chk_escrow_platform_fee CHECK (platform_fee_cents <= amount_cents);

CREATE TABLE escrow_disputes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    escrow_id BIGINT UNSIGNED NOT NULL,
    opened_by_user_id BIGINT UNSIGNED NOT NULL,
    reason VARCHAR(2000) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'open',
    resolution VARCHAR(32) NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    resolved_at TIMESTAMP(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_escrow_dispute_public_id (public_id),
    KEY idx_escrow_dispute_escrow_status (escrow_id,status),
    KEY idx_escrow_dispute_opened_by (opened_by_user_id,created_at),
    CONSTRAINT fk_escrow_dispute_escrow FOREIGN KEY (escrow_id) REFERENCES escrow_payments(id) ON DELETE RESTRICT,
    CONSTRAINT fk_escrow_dispute_user FOREIGN KEY (opened_by_user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT chk_escrow_dispute_status CHECK (status IN ('open','resolved')),
    CONSTRAINT chk_escrow_dispute_resolution CHECK (resolution IS NULL OR resolution IN ('pay_worker','refund_payer','split_settlement'))
) ENGINE=InnoDB;

ALTER TABLE escrow_payments
    ADD CONSTRAINT fk_escrow_dispute FOREIGN KEY (dispute_id) REFERENCES escrow_disputes(id) ON DELETE RESTRICT;
