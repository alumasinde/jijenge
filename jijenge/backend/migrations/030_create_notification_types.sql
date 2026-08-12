CREATE TABLE notification_types (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(500) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_notification_types_code (code),
    UNIQUE KEY uq_notification_types_name (name),
    KEY idx_notification_types_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO notification_types (code, name, description) VALUES
('JOB_CREATED', 'Job Created', 'A new job was created.'),
('APPLICATION_RECEIVED', 'Application Received', 'A provider applied to a job.'),
('APPLICATION_ACCEPTED', 'Application Accepted', 'A provider application was accepted.'),
('APPLICATION_REJECTED', 'Application Rejected', 'A provider application was rejected.'),
('APPLICATION_WITHDRAWN', 'Application Withdrawn', 'A provider withdrew an application.'),
('JOB_ASSIGNED', 'Job Assigned', 'A provider was assigned to a job.'),
('JOB_ON_THE_WAY', 'Provider On The Way', 'The assigned provider is travelling to the job.'),
('JOB_STARTED', 'Job Started', 'The provider started the job.'),
('JOB_COMPLETED', 'Job Completed', 'The job was completed.'),
('JOB_CANCELLED', 'Job Cancelled', 'The job was cancelled.'),
('SYSTEM', 'System Notification', 'A system notification.');
