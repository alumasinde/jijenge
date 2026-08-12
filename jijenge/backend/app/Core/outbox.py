import json

from app.database import db_connection


class OutboxRepository:
    def add(
        self,
        *,
        event_key: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: int,
        payload: dict,
    ) -> int:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id
                FROM outbox_event_statuses
                WHERE code = 'PENDING'
                LIMIT 1
                """
            )
            status_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO outbox_events
                    (
                        event_key,
                        event_type,
                        aggregate_type,
                        aggregate_id,
                        payload_json,
                        status_id
                    )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    id = LAST_INSERT_ID(id)
                """,
                (
                    event_key,
                    event_type,
                    aggregate_type,
                    aggregate_id,
                    json.dumps(payload),
                    status_id,
                ),
            )
            event_id = int(cursor.lastrowid)
            connection.commit()
            cursor.close()
            return event_id
