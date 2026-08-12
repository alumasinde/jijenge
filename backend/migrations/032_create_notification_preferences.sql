CREATE TABLE notification_channels (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(40) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_notification_channels_code (code),
    UNIQUE KEY uq_notification_channels_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO notification_channels (code, name) VALUES
('IN_APP', 'In-App'),
('EMAIL', 'Email'),
('SMS', 'SMS'),
('PUSH', 'Push');

CREATE TABLE notification_preferences (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    notification_type_id SMALLINT UNSIGNED NOT NULL,
    channel_id SMALLINT UNSIGNED NOT NULL,
    is_enabled TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_notification_preferences (
        user_id, notification_type_id, channel_id
    ),
    KEY idx_notification_preferences_user (
        user_id, is_enabled
    ),

    CONSTRAINT fk_notification_preferences_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_notification_preferences_type
        FOREIGN KEY (notification_type_id)
        REFERENCES notification_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_notification_preferences_channel
        FOREIGN KEY (channel_id)
        REFERENCES notification_channels (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
