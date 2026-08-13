import json

from app.database import db_connection


class PublicContentRepository:
    def get_public(self, locale: str):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT content_key, locale, content_type, content_value, sort_order
                    FROM public_content
                    WHERE locale=%s AND is_active=1
                    ORDER BY sort_order ASC, id ASC
                    """,
                    (locale,),
                )
                return [self._public_row(row) for row in cursor.fetchall()]
            finally:
                cursor.close()

    def list_admin(self, locale: str | None = None, active_only: bool = False, search: str | None = None):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                clauses = []
                params: list[object] = []
                if locale:
                    clauses.append("locale=%s")
                    params.append(locale)
                if active_only:
                    clauses.append("is_active=1")
                if search:
                    clauses.append("content_key LIKE %s")
                    params.append(f"%{search}%")
                where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
                cursor.execute(
                    f"""
                    SELECT id, content_key, locale, content_type, content_value,
                           is_active, sort_order, created_at, updated_at
                    FROM public_content
                    {where}
                    ORDER BY locale ASC, sort_order ASC, id ASC
                    """,
                    tuple(params),
                )
                return [self._admin_row(row) for row in cursor.fetchall()]
            finally:
                cursor.close()

    def get(self, content_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM public_content WHERE id=%s LIMIT 1", (content_id,))
                row = cursor.fetchone()
                return self._admin_row(row) if row else None
            finally:
                cursor.close()

    def create(self, data: dict):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    INSERT INTO public_content
                      (content_key, locale, content_type, content_value, is_active, sort_order)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    (data["content_key"], data["locale"], data["content_type"], json.dumps(data["content_value"], ensure_ascii=False), int(data["is_active"]), data["sort_order"]),
                )
                connection.commit()
                content_id = cursor.lastrowid
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        return self.get(content_id)

    def update(self, content_id: int, data: dict):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    UPDATE public_content
                    SET content_key=%s, locale=%s, content_type=%s, content_value=%s,
                        is_active=%s, sort_order=%s, updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,
                    (data["content_key"], data["locale"], data["content_type"], json.dumps(data["content_value"], ensure_ascii=False), int(data["is_active"]), data["sort_order"], content_id),
                )
                if cursor.rowcount == 0:
                    connection.rollback()
                    return None
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        return self.get(content_id)

    def delete(self, content_id: int) -> bool:
        with db_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("DELETE FROM public_content WHERE id=%s", (content_id,))
                deleted = cursor.rowcount > 0
                connection.commit()
                return deleted
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    @staticmethod
    def _decode(value):
        if isinstance(value, (bytes, bytearray)):
            value = value.decode("utf-8")
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    @classmethod
    def _public_row(cls, row):
        return {"key": row["content_key"], "value": cls._decode(row["content_value"]), "locale": row["locale"], "content_type": row["content_type"], "sort_order": row["sort_order"]}

    @classmethod
    def _admin_row(cls, row):
        if not row:
            return None
        for field in ("created_at", "updated_at"):
            if row.get(field) is not None and hasattr(row[field], "isoformat"):
                row[field] = row[field].isoformat()
        row["value"] = cls._decode(row.pop("content_value"))
        row["is_active"] = bool(row["is_active"])
        return row
