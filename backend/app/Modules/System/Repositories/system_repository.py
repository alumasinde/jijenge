import json

from app.database import db_connection


class SystemRepository:
    def list_settings(self, public_only: bool = False):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            if public_only:
                cursor.execute(
                    "SELECT * FROM system_settings WHERE is_public=1 ORDER BY setting_key"
                )
            else:
                cursor.execute("SELECT * FROM system_settings ORDER BY setting_key")
            rows = cursor.fetchall()
            cursor.close()
        return [self._normalize(row) for row in rows]

    def get_setting(self, key: str, public_only: bool = False):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            sql = "SELECT * FROM system_settings WHERE setting_key=%s"
            params = [key]
            if public_only:
                sql += " AND is_public=1"
            sql += " LIMIT 1"
            cursor.execute(sql, params)
            row = cursor.fetchone()
            cursor.close()
        return self._normalize(row) if row else None

    def upsert_setting(self, key: str, data: dict):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                value_json = json.dumps(data["value"])
                cursor.execute(
                    "SELECT id FROM system_settings WHERE setting_key=%s LIMIT 1", (key,)
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute(
                        """
                        UPDATE system_settings
                        SET value_json=%s, value_type=%s, description=%s,
                            is_public=%s, updated_at=CURRENT_TIMESTAMP
                        WHERE setting_key=%s
                        """,
                        (value_json, data["value_type"], data.get("description"),
                         data["is_public"], key),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO system_settings
                            (setting_key, value_json, value_type, description, is_public, is_editable)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (key, value_json, data["value_type"], data.get("description"),
                         data["is_public"], True),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        return self.get_setting(key)

    def delete_setting(self, key: str) -> bool:
        with db_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("DELETE FROM system_settings WHERE setting_key=%s", (key,))
                deleted = cursor.rowcount > 0
                connection.commit()
                return deleted
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    @staticmethod
    def _normalize(row):
        if not row:
            return None
        value = row["value_json"]
        if isinstance(value, str):
            value = json.loads(value)
        row["value"] = value
        del row["value_json"]
        row["is_public"] = bool(row["is_public"])
        row["is_editable"] = bool(row["is_editable"])
        return row
