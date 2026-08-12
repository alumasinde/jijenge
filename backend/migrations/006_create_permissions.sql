CREATE TABLE permissions (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(255) NULL,
    module VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_permissions_code (code),
    UNIQUE KEY uq_permissions_name (name),
    KEY idx_permissions_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO permissions (code, name, description, module) VALUES
('USER_VIEW', 'View users', 'View user records.', 'USERS'),
('USER_CREATE', 'Create users', 'Create user records.', 'USERS'),
('USER_UPDATE', 'Update users', 'Update user records.', 'USERS'),
('USER_DISABLE', 'Disable users', 'Disable user accounts.', 'USERS'),
('JOB_VIEW', 'View jobs', 'View job records.', 'JOBS'),
('JOB_CREATE', 'Create jobs', 'Create job requests.', 'JOBS'),
('JOB_UPDATE', 'Update jobs', 'Update job requests.', 'JOBS');
