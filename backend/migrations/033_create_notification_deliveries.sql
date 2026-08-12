CREATE TABLE notification_delivery_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(40) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_notification_delivery_statuses_code (code),
    UNIQUE KEY uq_notification_delivery_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO notification_delivery_statuses (code, name) VALUES
('PENDING', 'Pending'),
('PROCESSING', 'Processing'),
('SENT', 'Sent'),
('FAILED', 'Failed'),
('SKIPPED', 'Skipped');

CREATE TABLE notification_deliveries (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    notification_id BIGINT UNSIGNED NOT NULL,
    channel_id SMALLINT UNSIGNED NOT NULL,
    delivery_status_id SMALLINT UNSIGNED NOT NULL,
    attempt_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    provider_message_id VARCHAR(255) NULL,
    last_error VARCHAR(2000) NULL,
    scheduled_at TIMESTAMP NULL,
    sent_at TIMESTAMP NULL,
    failed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_notification_delivery_channel (
        notification_id, channel_id
    ),
    KEY idx_notification_deliveries_status_scheduled (
        delivery_status_id, scheduled_at, id
    ),
    KEY idx_notification_deliveries_notification (
        notification_id
    ),

    CONSTRAINT fk_notification_deliveries_notification
        FOREIGN KEY (notification_id)
        REFERENCES notifications (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_notification_deliveries_channel
        FOREIGN KEY (channel_id)
        REFERENCES notification_channels (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_notification_deliveries_status
        FOREIGN KEY (delivery_status_id)
        REFERENCES notification_delivery_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_notification_delivery_attempts
        CHECK (attempt_count >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
