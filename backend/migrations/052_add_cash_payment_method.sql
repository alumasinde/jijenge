INSERT INTO payment_methods
    (code, name, provider_code, is_active, sort_order)
VALUES
    ('CASH', 'Cash', NULL, 1, 20)
ON DUPLICATE KEY UPDATE
    is_active = 1,
    sort_order = 20;
