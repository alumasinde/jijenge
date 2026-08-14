CREATE TABLE authorization_audit_log (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    actor_user_id BIGINT UNSIGNED NULL,
    action VARCHAR(64) NOT NULL,
    target_user_id BIGINT UNSIGNED NULL,
    role_id BIGINT UNSIGNED NULL,
    permission_id BIGINT UNSIGNED NULL,
    reason VARCHAR(500) NULL,
    request_id VARCHAR(128) NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_auth_audit_actor_created (actor_user_id, created_at),
    KEY idx_auth_audit_target_created (target_user_id, created_at),
    CONSTRAINT fk_auth_audit_actor FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_auth_audit_target FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_auth_audit_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL,
    CONSTRAINT fk_auth_audit_permission FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE SET NULL
) ENGINE=InnoDB;
