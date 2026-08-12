CREATE TABLE brandings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    brand_code VARCHAR(80) NOT NULL DEFAULT 'default',
    app_name VARCHAR(150) NOT NULL,
    short_name VARCHAR(80) NOT NULL,
    tagline VARCHAR(255) NULL,
    logo_url VARCHAR(1000) NULL,
    logo_dark_url VARCHAR(1000) NULL,
    favicon_url VARCHAR(1000) NULL,
    primary_color CHAR(7) NOT NULL DEFAULT '#2563EB',
    secondary_color CHAR(7) NOT NULL DEFAULT '#1E40AF',
    accent_color CHAR(7) NOT NULL DEFAULT '#F59E0B',
    background_color CHAR(7) NOT NULL DEFAULT '#F8FAFC',
    surface_color CHAR(7) NOT NULL DEFAULT '#FFFFFF',
    text_color CHAR(7) NOT NULL DEFAULT '#0F172A',
    muted_color CHAR(7) NOT NULL DEFAULT '#64748B',
    border_color CHAR(7) NOT NULL DEFAULT '#E2E8F0',
    success_color CHAR(7) NOT NULL DEFAULT '#16A34A',
    warning_color CHAR(7) NOT NULL DEFAULT '#D97706',
    danger_color CHAR(7) NOT NULL DEFAULT '#DC2626',
    info_color CHAR(7) NOT NULL DEFAULT '#0284C7',
    font_family VARCHAR(150) NOT NULL DEFAULT 'Inter, system-ui, sans-serif',
    border_radius VARCHAR(20) NOT NULL DEFAULT '0.75rem',
    dark_mode_enabled TINYINT(1) NOT NULL DEFAULT 1,
    dark_theme_json JSON NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_brandings_code (brand_code),
    KEY idx_brandings_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO brandings (
    brand_code, app_name, short_name, tagline
) VALUES (
    'default', 'Jijenge', 'Jijenge', 'Find trusted services and get things done.'
);
