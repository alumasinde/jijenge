CREATE TABLE notifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    recipient_user_id BIGINT UNSIGNED NOT NULL,
    notification_type_id SMALLINT UNSIGNED NOT NULL,
    title VARCHAR(200) NOT NULL,
    body VARCHAR(2000) NOT NULL,
    entity_type VARCHAR(80) NULL,
    entity_id BIGINT UNSIGNED NULL,
    data_json JSON NULL,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,

    PRIMARY KEY (id),
    KEY idx_notifications_recipient_created (
        recipient_user_id, created_at, id
    ),
    KEY idx_notifications_recipient_unread (
        recipient_user_id, read_at, created_at
    ),
    KEY idx_notifications_type_created (
        notification_type_id, created_at
    ),
    KEY idx_notifications_entity (
        entity_type, entity_id
    ),

    CONSTRAINT fk_notifications_recipient
        FOREIGN KEY (recipient_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_notifications_type
        FOREIGN KEY (notification_type_id)
        REFERENCES notification_types (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
