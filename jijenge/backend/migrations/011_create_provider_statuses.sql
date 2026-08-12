CREATE TABLE provider_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_statuses_code (code),
    UNIQUE KEY uq_provider_statuses_name (name),
    KEY idx_provider_statuses_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO provider_statuses (code, name, description, sort_order) VALUES
('PENDING', 'Pending', 'Provider onboarding is awaiting review.', 10),
('ACTIVE', 'Active', 'Provider can receive service opportunities.', 20),
('SUSPENDED', 'Suspended', 'Provider is temporarily unavailable.', 30),
('DISABLED', 'Disabled', 'Provider profile is disabled.', 40);
