CREATE TABLE payment_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_payment_statuses_code (code),
    UNIQUE KEY uq_payment_statuses_name (name),
    KEY idx_payment_statuses_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO payment_statuses
    (code, name, description, is_terminal, is_success, sort_order)
VALUES
    ('CREATED', 'Created', 'Payment intent has been created.', 0, 0, 10),
    ('PENDING', 'Pending', 'Payment is awaiting provider confirmation.', 0, 0, 20),
    ('PROCESSING', 'Processing', 'Payment provider is processing the transaction.', 0, 0, 30),
    ('SUCCEEDED', 'Succeeded', 'Payment was successfully completed.', 1, 1, 40),
    ('FAILED', 'Failed', 'Payment failed.', 1, 0, 50),
    ('CANCELLED', 'Cancelled', 'Payment was cancelled.', 1, 0, 60),
    ('EXPIRED', 'Expired', 'Payment request expired.', 1, 0, 70),
    ('REFUNDED', 'Refunded', 'Payment was refunded.', 1, 0, 80),
    ('PARTIALLY_REFUNDED', 'Partially Refunded', 'Part of the payment was refunded.', 0, 0, 90);
