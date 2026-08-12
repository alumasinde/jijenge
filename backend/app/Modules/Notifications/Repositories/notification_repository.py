import json

from app.database import db_connection


class NotificationRepository:
    def create(
        self,
        recipient_user_id: int,
        notification_type: str,
        title: str,
        body: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        data: dict | None = None,
    ) -> int:
        with db_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT id
                    FROM notification_types
                    WHERE code = %s AND is_active = 1
                    LIMIT 1
                    """,
                    (notification_type,),
                )
                notification_type_row = cursor.fetchone()
                if not notification_type_row:
                    raise ValueError(f"Unknown notification type: {notification_type}")

                cursor.execute(
                    """
                    INSERT INTO notifications
                        (
                            recipient_user_id,
                            notification_type_id,
                            title,
                            body,
                            entity_type,
                            entity_id,
                            data_json
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        recipient_user_id,
                        notification_type_row[0],
                        title,
                        body,
                        entity_type,
                        entity_id,
                        json.dumps(data) if data is not None else None,
                    ),
                )
                notification_id = int(cursor.lastrowid)

                cursor.execute(
                    """
                    SELECT id
                    FROM notification_channels
                    WHERE code = 'IN_APP' AND is_active = 1
                    LIMIT 1
                    """
                )
                channel = cursor.fetchone()

                cursor.execute(
                    """
                    SELECT id
                    FROM notification_delivery_statuses
                    WHERE code = 'PENDING' AND is_active = 1
                    LIMIT 1
                    """
                )
                pending_status = cursor.fetchone()

                if channel and pending_status:
                    cursor.execute(
                        """
                        INSERT INTO notification_deliveries
                            (
                                notification_id,
                                channel_id,
                                delivery_status_id,
                                scheduled_at
                            )
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        ON DUPLICATE KEY UPDATE
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (notification_id, channel[0], pending_status[0]),
                    )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return notification_id

    def list_for_user(self, user_id: int, limit: int, offset: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    n.id,
                    nt.code AS notification_type,
                    n.title,
                    n.body,
                    n.entity_type,
                    n.entity_id,
                    n.data_json,
                    n.read_at,
                    n.created_at
                FROM notifications n
                INNER JOIN notification_types nt
                    ON nt.id = n.notification_type_id
                WHERE n.recipient_user_id = %s
                  AND (n.expires_at IS NULL OR n.expires_at > CURRENT_TIMESTAMP)
                ORDER BY n.created_at DESC, n.id DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
            rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM notifications
                WHERE recipient_user_id = %s
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """,
                (user_id,),
            )
            total = int(cursor.fetchone()["total"])

            cursor.execute(
                """
                SELECT COUNT(*) AS unread_count
                FROM notifications
                WHERE recipient_user_id = %s
                  AND read_at IS NULL
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """,
                (user_id,),
            )
            unread_count = int(cursor.fetchone()["unread_count"])

            cursor.close()
            return rows, total, unread_count

    def mark_read(self, user_id: int, notification_id: int) -> bool:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE notifications
                SET read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
                WHERE id = %s
                  AND recipient_user_id = %s
                """,
                (notification_id, user_id),
            )
            changed = cursor.rowcount > 0
            connection.commit()
            cursor.close()
            return changed

    def mark_all_read(self, user_id: int) -> int:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE notifications
                SET read_at = CURRENT_TIMESTAMP
                WHERE recipient_user_id = %s
                  AND read_at IS NULL
                """,
                (user_id,),
            )
            changed = cursor.rowcount
            connection.commit()
            cursor.close()
            return changed

    def register_device(
        self,
        user_id: int,
        platform: str,
        token: str,
        device_name: str | None,
        app_version: str | None,
    ):
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO device_tokens
                    (
                        user_id, platform, token,
                        device_name, app_version,
                        is_active, last_seen_at
                    )
                VALUES
                    (%s, %s, %s, %s, %s, 1, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE
                    user_id = VALUES(user_id),
                    platform = VALUES(platform),
                    device_name = VALUES(device_name),
                    app_version = VALUES(app_version),
                    is_active = 1,
                    last_seen_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id, platform, token,
                    device_name, app_version,
                ),
            )
            connection.commit()
            cursor.close()

    def deactivate_device(self, user_id: int, token: str) -> bool:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE device_tokens
                SET is_active = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                  AND token = %s
                """,
                (user_id, token),
            )
            changed = cursor.rowcount > 0
            connection.commit()
            cursor.close()
            return changed
