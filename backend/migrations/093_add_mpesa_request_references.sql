ALTER TABLE payment_provider_requests
    ADD COLUMN merchant_request_id VARCHAR(255) NULL AFTER provider_request_id,
    ADD COLUMN checkout_request_id VARCHAR(255) NULL AFTER merchant_request_id,
    ADD KEY idx_payment_provider_requests_checkout (
        provider_code,checkout_request_id
    ),
    ADD KEY idx_payment_provider_requests_merchant (
        provider_code,merchant_request_id
    );
