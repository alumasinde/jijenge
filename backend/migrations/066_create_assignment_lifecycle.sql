CREATE TABLE IF NOT EXISTS assignment_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_assignment_statuses_code (code),
    UNIQUE KEY uq_assignment_statuses_name (name),
    KEY idx_assignment_statuses_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO assignment_statuses
    (code, name, is_terminal, is_success, sort_order)
VALUES
    ('PENDING_PROVIDER_CONFIRMATION', 'Pending Provider Confirmation', 0, 0, 10),
    ('CONFIRMED', 'Confirmed', 0, 1, 20),
    ('PROVIDER_DECLINED', 'Provider Declined', 1, 0, 30),
    ('CANCELLED', 'Cancelled', 1, 0, 40),
    ('IN_PROGRESS', 'In Progress', 0, 1, 50),
    ('COMPLETED', 'Completed', 1, 1, 60),
    ('FAILED', 'Failed', 1, 0, 70)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    is_terminal = VALUES(is_terminal),
    is_success = VALUES(is_success),
    is_active = VALUES(is_active),
    sort_order = VALUES(sort_order);

-- Use INFORMATION_SCHEMA + prepared statements for conditional column changes.
-- This lets the migration finish safely after a partial earlier attempt.
-- safely finish a database where an earlier attempt partially ran.
SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name = 'job_assignments'
       AND column_name = 'status_id') = 0,
    'ALTER TABLE job_assignments ADD COLUMN status_id SMALLINT UNSIGNED NULL AFTER application_id',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name = 'job_assignments'
       AND column_name = 'confirmation_deadline') = 0,
    'ALTER TABLE job_assignments ADD COLUMN confirmation_deadline TIMESTAMP NULL AFTER assigned_at',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name = 'job_assignments'
       AND column_name = 'confirmed_at') = 0,
    'ALTER TABLE job_assignments ADD COLUMN confirmed_at TIMESTAMP NULL AFTER confirmation_deadline',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name = 'job_assignments'
       AND column_name = 'declined_at') = 0,
    'ALTER TABLE job_assignments ADD COLUMN declined_at TIMESTAMP NULL AFTER confirmed_at',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name = 'job_assignments'
       AND column_name = 'decline_reason') = 0,
    'ALTER TABLE job_assignments ADD COLUMN decline_reason VARCHAR(1000) NULL AFTER declined_at',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE job_assignments ja
INNER JOIN assignment_statuses ass
    ON ass.code = 'CONFIRMED'
SET ja.status_id = ass.id,
    ja.confirmed_at = COALESCE(ja.confirmed_at, ja.assigned_at)
WHERE ja.status_id IS NULL;

ALTER TABLE job_assignments
    MODIFY COLUMN status_id SMALLINT UNSIGNED NOT NULL;

SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.statistics
     WHERE table_schema = DATABASE()
       AND table_name = 'job_assignments'
       AND index_name = 'idx_job_assignments_status_deadline') = 0,
    'ALTER TABLE job_assignments ADD KEY idx_job_assignments_status_deadline (status_id, confirmation_deadline, id)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.statistics
     WHERE table_schema = DATABASE()
       AND table_name = 'job_assignments'
       AND index_name = 'idx_job_assignments_provider_status') = 0,
    'ALTER TABLE job_assignments ADD KEY idx_job_assignments_provider_status (provider_id, status_id, cancelled_at, completed_at)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.referential_constraints
     WHERE constraint_schema = DATABASE()
       AND table_name = 'job_assignments'
       AND constraint_name = 'fk_job_assignments_status') = 0,
    'ALTER TABLE job_assignments ADD CONSTRAINT fk_job_assignments_status FOREIGN KEY (status_id) REFERENCES assignment_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
