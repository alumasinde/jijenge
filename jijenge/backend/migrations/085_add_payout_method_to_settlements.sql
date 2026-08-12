ALTER TABLE provider_settlements
    ADD COLUMN provider_payout_method_id BIGINT UNSIGNED NULL AFTER payout_method_id,
    ADD KEY idx_provider_settlements_payout_method (
        provider_payout_method_id
    ),
    ADD CONSTRAINT fk_provider_settlements_provider_payout_method
        FOREIGN KEY (provider_payout_method_id)
        REFERENCES provider_payout_methods(id)
        ON UPDATE RESTRICT ON DELETE SET NULL;
