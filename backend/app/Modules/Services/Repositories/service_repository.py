from app.database import db_connection


class ServiceRepository:
    def list_categories(self) -> list[dict]:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, code, name, description
                FROM service_categories
                WHERE is_active = 1
                ORDER BY sort_order, name
                """
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def list_services(self, category_id: int | None = None) -> list[dict]:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    s.id,
                    s.category_id,
                    c.code AS category_code,
                    c.name AS category_name,
                    s.code,
                    s.name,
                    s.description
                FROM services s
                INNER JOIN service_categories c ON c.id = s.category_id
                WHERE s.is_active = 1
                  AND c.is_active = 1
            """
            params: list = []

            if category_id is not None:
                query += " AND s.category_id = %s"
                params.append(category_id)

            query += " ORDER BY c.sort_order, c.name, s.sort_order, s.name"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows
