CREATE TABLE services (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    category_id INT UNSIGNED NOT NULL,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(180) NOT NULL,
    description VARCHAR(1000) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_services_code (code),
    UNIQUE KEY uq_services_category_name (category_id, name),
    KEY idx_services_category_active (category_id, is_active, sort_order),
    KEY idx_services_active_sort (is_active, sort_order),

    CONSTRAINT fk_services_category
        FOREIGN KEY (category_id)
        REFERENCES service_categories (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO services (category_id, code, name, description, sort_order)
SELECT id, 'PLUMBING', 'Plumbing', 'Plumbing installation, maintenance and repair.', 10
FROM service_categories WHERE code = 'HOME_REPAIR';

INSERT INTO services (category_id, code, name, description, sort_order)
SELECT id, 'ELECTRICAL', 'Electrical Services', 'Residential electrical installation, maintenance and repair.', 20
FROM service_categories WHERE code = 'HOME_REPAIR';

INSERT INTO services (category_id, code, name, description, sort_order)
SELECT id, 'PAINTING', 'Painting', 'Interior and exterior painting services.', 30
FROM service_categories WHERE code = 'HOME_REPAIR';

INSERT INTO services (category_id, code, name, description, sort_order)
SELECT id, 'HOUSE_CLEANING', 'House Cleaning', 'Routine and deep house cleaning.', 10
FROM service_categories WHERE code = 'CLEANING';

INSERT INTO services (category_id, code, name, description, sort_order)
SELECT id, 'OFFICE_CLEANING', 'Office Cleaning', 'Office and workplace cleaning.', 20
FROM service_categories WHERE code = 'CLEANING';

INSERT INTO services (category_id, code, name, description, sort_order)
SELECT id, 'MOVING_HELP', 'Moving Help', 'Loading, unloading and household moving assistance.', 10
FROM service_categories WHERE code = 'MOVING';

INSERT INTO services (category_id, code, name, description, sort_order)
SELECT id, 'SALON_SERVICES', 'Salon Services', 'Hair and general salon services.', 10
FROM service_categories WHERE code = 'BEAUTY';

INSERT INTO services (category_id, code, name, description, sort_order)
SELECT id, 'PHONE_REPAIR', 'Phone Repair', 'Mobile phone diagnostics and repair.', 10
FROM service_categories WHERE code = 'TECHNOLOGY';

INSERT INTO services (category_id, code, name, description, sort_order)
SELECT id, 'COMPUTER_SUPPORT', 'Computer Support', 'Computer setup, troubleshooting and support.', 20
FROM service_categories WHERE code = 'TECHNOLOGY';
