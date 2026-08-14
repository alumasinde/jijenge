
CREATE TABLE notifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    channel VARCHAR(16) NOT NULL,
    title VARCHAR(200) NOT NULL,
    body VARCHAR(5000) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    reference_type VARCHAR(64) NULL,
    reference_id VARCHAR(128) NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'unread',
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    read_at TIMESTAMP(6) NULL,
    PRIMARY KEY(id),
    UNIQUE KEY uq_notifications_public_id(public_id),
    KEY idx_notifications_user_status_created(user_id,status,created_at,id),
    KEY idx_notifications_user_created(user_id,created_at,id),
    KEY idx_notifications_reference(reference_type,reference_id),
    CONSTRAINT fk_notifications_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_notifications_channel CHECK(channel IN ('in_app','email','sms','push')),
    CONSTRAINT chk_notifications_status CHECK(status IN ('unread','read'))
) ENGINE=InnoDB;

CREATE TABLE notification_preferences (
    user_id BIGINT UNSIGNED NOT NULL,
    channel VARCHAR(16) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY(user_id,channel,event_type),
    CONSTRAINT fk_notification_preferences_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_notification_preferences_channel CHECK(channel IN ('in_app','email','sms','push'))
) ENGINE=InnoDB;

CREATE TABLE notification_outbox (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    notification_id BIGINT UNSIGNED NOT NULL,
    channel VARCHAR(16) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    attempts SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    available_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    locked_at TIMESTAMP(6) NULL,
    sent_at TIMESTAMP(6) NULL,
    last_error VARCHAR(1000) NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY(id),
    UNIQUE KEY uq_notification_outbox_public_id(public_id),
    UNIQUE KEY uq_notification_outbox_notification_channel(notification_id,channel),
    KEY idx_notification_outbox_work(status,available_at,id),
    CONSTRAINT fk_notification_outbox_notification FOREIGN KEY(notification_id) REFERENCES notifications(id) ON DELETE RESTRICT,
    CONSTRAINT chk_notification_outbox_channel CHECK(channel IN ('email','sms','push')),
    CONSTRAINT chk_notification_outbox_status CHECK(status IN ('pending','processing','sent','failed'))
) ENGINE=InnoDB;
