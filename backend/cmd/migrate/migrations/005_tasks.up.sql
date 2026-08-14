CREATE TABLE task_categories (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(140) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_task_categories_name (name),
    UNIQUE KEY uq_task_categories_slug (slug)
) ENGINE=InnoDB;

CREATE TABLE tasks (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    owner_user_id BIGINT UNSIGNED NOT NULL,
    category_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(5000) NOT NULL,
    budget_cents BIGINT UNSIGNED NOT NULL,
    currency CHAR(3) NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_tasks_public_id (public_id),
    KEY idx_tasks_owner_status (owner_user_id,status,created_at),
    KEY idx_tasks_category_status (category_id,status,created_at),
    CONSTRAINT fk_tasks_owner FOREIGN KEY (owner_user_id) REFERENCES users(id),
    CONSTRAINT fk_tasks_category FOREIGN KEY (category_id) REFERENCES task_categories(id)
) ENGINE=InnoDB;

CREATE TABLE task_applications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_id BIGINT UNSIGNED NOT NULL,
    applicant_user_id BIGINT UNSIGNED NOT NULL,
    message VARCHAR(2000) NOT NULL,
    proposed_cents BIGINT UNSIGNED NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_task_application_user (task_id,applicant_user_id),
    KEY idx_task_applications_task_status (task_id,status,created_at),
    KEY idx_task_applications_user_status (applicant_user_id,status,created_at),
    CONSTRAINT fk_task_applications_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    CONSTRAINT fk_task_applications_user FOREIGN KEY (applicant_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE task_assignments (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_id BIGINT UNSIGNED NOT NULL,
    application_id BIGINT UNSIGNED NOT NULL,
    worker_user_id BIGINT UNSIGNED NOT NULL,
    assigned_by_user_id BIGINT UNSIGNED NOT NULL,
    status VARCHAR(32) NOT NULL,
    submitted_at TIMESTAMP(6) NULL,
    verified_at TIMESTAMP(6) NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_task_assignment_application (application_id),
    KEY idx_task_assignments_worker_status (worker_user_id,status,created_at),
    KEY idx_task_assignments_task_status (task_id,status),
    CONSTRAINT fk_task_assignments_task FOREIGN KEY (task_id) REFERENCES tasks(id),
    CONSTRAINT fk_task_assignments_application FOREIGN KEY (application_id) REFERENCES task_applications(id),
    CONSTRAINT fk_task_assignments_worker FOREIGN KEY (worker_user_id) REFERENCES users(id),
    CONSTRAINT fk_task_assignments_assigner FOREIGN KEY (assigned_by_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE task_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_id BIGINT UNSIGNED NOT NULL,
    actor_user_id BIGINT UNSIGNED NULL,
    event_type VARCHAR(64) NOT NULL,
    from_status VARCHAR(32) NULL,
    to_status VARCHAR(32) NULL,
    metadata JSON NULL,
    request_id VARCHAR(128) NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_task_events_task_created (task_id,created_at),
    KEY idx_task_events_actor_created (actor_user_id,created_at),
    CONSTRAINT fk_task_events_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    CONSTRAINT fk_task_events_actor FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;
