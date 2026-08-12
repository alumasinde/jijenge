import json
import uuid

from app.database import db_connection


class TrustRepository:
    _ALLOWED_TABLES = frozenset({'trust_report_statuses', 'trust_report_types'})

    def _id(self, cursor, table, code):
        if table not in self._ALLOWED_TABLES:
            raise ValueError("Unsupported lookup table")
        sql = (
            "SELECT id FROM " + table +
            " WHERE code = %s AND is_active = 1 LIMIT 1"
        )
        cursor.execute(sql, (code,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"{table} value {code} is missing")
        return int(row["id"])

    def create_report(self, reporter_user_id: int, data):
        if not any([
            data.reported_user_id,
            data.job_id,
            data.review_id,
        ]):
            raise ValueError(
                "A report must reference a user, job, or review"
            )

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                report_type_id = self._id(
                    cursor,
                    "trust_report_types",
                    data.report_type_code.strip().upper(),
                )
                status_id = self._id(
                    cursor,
                    "trust_report_statuses",
                    "OPEN",
                )

                public_id = str(uuid.uuid4())

                cursor.execute(
                    """
                    INSERT INTO trust_reports
                        (
                            public_id,
                            reporter_user_id,
                            report_type_id,
                            status_id,
                            reported_user_id,
                            job_id,
                            review_id,
                            description,
                            evidence_json
                        )
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        public_id,
                        reporter_user_id,
                        report_type_id,
                        status_id,
                        data.reported_user_id,
                        data.job_id,
                        data.review_id,
                        data.description.strip(),
                        json.dumps(data.evidence),
                    ),
                )
                report_id = int(cursor.lastrowid)
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return {
            "id": report_id,
            "public_id": public_id,
            "status": "OPEN",
        }
