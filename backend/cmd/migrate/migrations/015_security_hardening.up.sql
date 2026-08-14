
ALTER TABLE sessions
    ADD COLUMN last_rotated_at TIMESTAMP(6) NULL AFTER last_seen_at,
    ADD KEY idx_sessions_expiry (expires_at, revoked_at);

ALTER TABLE admin_action_requests
    ADD KEY idx_admin_action_approval(approved_by,status,approved_at);

CREATE TABLE security_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    user_id BIGINT UNSIGNED NULL,
    event_type VARCHAR(64) NOT NULL,
    request_id VARCHAR(128) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(512) NULL,
    metadata JSON NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY(id),
    UNIQUE KEY uq_security_events_public_id(public_id),
    KEY idx_security_events_user_created(user_id,created_at,id),
    KEY idx_security_events_type_created(event_type,created_at,id),
    KEY idx_security_events_request(request_id),
    CONSTRAINT fk_security_events_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;
