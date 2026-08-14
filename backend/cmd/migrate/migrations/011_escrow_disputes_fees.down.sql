
ALTER TABLE escrow_payments DROP FOREIGN KEY fk_escrow_dispute;
ALTER TABLE escrow_payments DROP COLUMN dispute_id;
ALTER TABLE escrow_payments DROP COLUMN platform_fee_cents;
DROP TABLE IF EXISTS escrow_disputes;
