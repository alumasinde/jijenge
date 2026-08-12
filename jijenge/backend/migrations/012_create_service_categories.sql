CREATE TABLE service_categories (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(500) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_service_categories_code (code),
    UNIQUE KEY uq_service_categories_name (name),
    KEY idx_service_categories_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO service_categories (code, name, description, sort_order) VALUES
('HOME_REPAIR', 'Home Repair', 'Repair and maintenance services for homes.', 10),
('CLEANING', 'Cleaning', 'Home, office and specialized cleaning services.', 20),
('MOVING', 'Moving', 'Moving, transport and related services.', 30),
('BEAUTY', 'Beauty', 'Beauty and personal care services.', 40),
('TECHNOLOGY', 'Technology', 'Technology installation, repair and support.', 50),
('PROFESSIONAL', 'Professional Services', 'Professional and business support services.', 60);
