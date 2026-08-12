from app.database import db_connection


class AvailabilityRepository:
    def _status_id(self, cursor, code: str) -> int:
        cursor.execute(
            """
            SELECT id FROM availability_rule_statuses
            WHERE code = %s AND is_active = 1 LIMIT 1
            """,
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Availability status {code} is missing")
        return int(row["id"])

    def add_rule(self, provider_id, data):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                status_id = self._status_id(cursor, "ACTIVE")
                cursor.execute(
                    """
                    INSERT INTO provider_availability_rules
                        (
                            provider_id, status_id, day_of_week,
                            start_time, end_time, effective_from, effective_to
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        provider_id, status_id, data.day_of_week,
                        data.start_time, data.end_time,
                        data.effective_from, data.effective_to,
                    ),
                )
                rule_id = cursor.lastrowid
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        return self.get_rule(provider_id, rule_id)

    def get_rule(self, provider_id, rule_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    par.id,
                    par.day_of_week,
                    par.start_time,
                    par.end_time,
                    par.effective_from,
                    par.effective_to,
                    ars.code AS status
                FROM provider_availability_rules par
                INNER JOIN availability_rule_statuses ars
                    ON ars.id = par.status_id
                WHERE par.id = %s AND par.provider_id = %s
                LIMIT 1
                """,
                (rule_id, provider_id),
            )
            row = cursor.fetchone()
            cursor.close()
        return row

    def list_rules(self, provider_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    par.id,
                    par.day_of_week,
                    par.start_time,
                    par.end_time,
                    par.effective_from,
                    par.effective_to,
                    ars.code AS status
                FROM provider_availability_rules par
                INNER JOIN availability_rule_statuses ars
                    ON ars.id = par.status_id
                WHERE par.provider_id = %s
                  AND ars.code = 'ACTIVE'
                ORDER BY par.day_of_week, par.start_time, par.id
                """,
                (provider_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows

    def add_exception(self, provider_id, data):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    INSERT INTO provider_availability_exceptions
                        (
                            provider_id, exception_date, is_available,
                            start_time, end_time, reason
                        )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        is_available = VALUES(is_available),
                        start_time = VALUES(start_time),
                        end_time = VALUES(end_time),
                        reason = VALUES(reason)
                    """,
                    (
                        provider_id, data.exception_date, int(data.is_available),
                        data.start_time, data.end_time, data.reason,
                    ),
                )
                exception_id = cursor.lastrowid
                if not exception_id:
                    cursor.execute(
                        """
                        SELECT id
                        FROM provider_availability_exceptions
                        WHERE provider_id = %s AND exception_date = %s
                        LIMIT 1
                        """,
                        (provider_id, data.exception_date),
                    )
                    exception_id = cursor.fetchone()["id"]
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        return self.get_exception(provider_id, exception_id)

    def get_exception(self, provider_id, exception_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id, exception_date, is_available,
                    start_time, end_time, reason
                FROM provider_availability_exceptions
                WHERE id = %s AND provider_id = %s
                LIMIT 1
                """,
                (exception_id, provider_id),
            )
            row = cursor.fetchone()
            cursor.close()
        return row

    def list_exceptions(self, provider_id, from_date, to_date):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id, exception_date, is_available,
                    start_time, end_time, reason
                FROM provider_availability_exceptions
                WHERE provider_id = %s
                  AND exception_date BETWEEN %s AND %s
                ORDER BY exception_date, id
                """,
                (provider_id, from_date, to_date),
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows

    def get_preferences(self, provider_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    provider_id,
                    max_distance_km,
                    accepts_new_jobs,
                    auto_match_enabled,
                    minimum_notice_minutes
                FROM provider_matching_preferences
                WHERE provider_id = %s
                LIMIT 1
                """,
                (provider_id,),
            )
            row = cursor.fetchone()
            cursor.close()
        return row

    def upsert_preferences(self, provider_id, data):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    INSERT INTO provider_matching_preferences
                        (
                            provider_id, max_distance_km,
                            accepts_new_jobs, auto_match_enabled,
                            minimum_notice_minutes
                        )
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        max_distance_km = VALUES(max_distance_km),
                        accepts_new_jobs = VALUES(accepts_new_jobs),
                        auto_match_enabled = VALUES(auto_match_enabled),
                        minimum_notice_minutes = VALUES(minimum_notice_minutes)
                    """,
                    (
                        provider_id, data.max_distance_km,
                        int(data.accepts_new_jobs),
                        int(data.auto_match_enabled),
                        data.minimum_notice_minutes,
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        return self.get_preferences(provider_id)

    def is_available_at(self, provider_id, target_dt):
        # Exceptions override recurring rules.
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT is_available, start_time, end_time
                FROM provider_availability_exceptions
                WHERE provider_id = %s
                  AND exception_date = %s
                LIMIT 1
                """,
                (provider_id, target_dt.date()),
            )
            exception = cursor.fetchone()
            if exception:
                cursor.close()
                if not exception["is_available"]:
                    return False
                return (
                    exception["start_time"] <= target_dt.time()
                    < exception["end_time"]
                )

            day_of_week = target_dt.isoweekday()
            cursor.execute(
                """
                SELECT 1
                FROM provider_availability_rules par
                INNER JOIN availability_rule_statuses ars
                    ON ars.id = par.status_id
                WHERE par.provider_id = %s
                  AND par.day_of_week = %s
                  AND ars.code = 'ACTIVE'
                  AND par.start_time <= %s
                  AND par.end_time > %s
                  AND (par.effective_from IS NULL OR par.effective_from <= %s)
                  AND (par.effective_to IS NULL OR par.effective_to >= %s)
                LIMIT 1
                """,
                (
                    provider_id, day_of_week,
                    target_dt.time(), target_dt.time(),
                    target_dt.date(), target_dt.date(),
                ),
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None
