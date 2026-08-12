-- Extend the original refund model from 047 with the job-payment/dispute
-- lifecycle used by the current refund and execution services.

INSERT INTO refund_statuses (code,name,is_terminal,is_success)
VALUES
('APPROVED','Approved',0,0),
('PAID','Paid',1,1),
('REJECTED','Rejected',1,0),
('REVERSED','Reversed',1,0)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    is_terminal = VALUES(is_terminal),
    is_success = VALUES(is_success);

ALTER TABLE refunds
    ADD COLUMN IF NOT EXISTS job_payment_record_id BIGINT UNSIGNED NULL AFTER payment_transaction_id,
    ADD COLUMN IF NOT EXISTS dispute_id BIGINT UNSIGNED NULL AFTER job_payment_record_id,
    ADD COLUMN IF NOT EXISTS requested_amount DECIMAL(14,2) NULL AFTER amount,
    ADD COLUMN IF NOT EXISTS approved_amount DECIMAL(14,2) NOT NULL DEFAULT 0 AFTER requested_amount,
    ADD COLUMN IF NOT EXISTS paid_amount DECIMAL(14,2) NOT NULL DEFAULT 0 AFTER approved_amount,
    ADD COLUMN IF NOT EXISTS requested_at TIMESTAMP NULL AFTER updated_at,
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP NULL AFTER requested_at,
    ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP NULL AFTER approved_at,
    ADD COLUMN IF NOT EXISTS failure_reason VARCHAR(1000) NULL AFTER paid_at;

-- The legacy payment-intent flow remains supported. New job-payment refunds
-- can leave the legacy payment_intent_id/amount fields empty.
ALTER TABLE refunds
    MODIFY COLUMN payment_intent_id BIGINT UNSIGNED NULL,
    MODIFY COLUMN requested_by_user_id BIGINT UNSIGNED NULL,
    MODIFY COLUMN amount DECIMAL(14,2) NULL;

UPDATE refunds
SET requested_amount = COALESCE(requested_amount, amount),
    requested_at = COALESCE(requested_at, created_at)
WHERE requested_amount IS NULL;

ALTER TABLE refunds
    ADD KEY idx_refunds_job_payment_status (job_payment_record_id,status_id,created_at),
    ADD KEY idx_refunds_dispute (dispute_id,status_id);

ALTER TABLE refunds
    ADD CONSTRAINT fk_refunds_job_payment
        FOREIGN KEY (job_payment_record_id) REFERENCES job_payment_records(id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT fk_refunds_dispute
        FOREIGN KEY (dispute_id) REFERENCES disputes(id)
        ON UPDATE RESTRICT ON DELETE SET NULL;
