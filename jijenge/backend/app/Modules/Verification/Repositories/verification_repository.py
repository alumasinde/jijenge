import uuid

from app.database import db_connection


class VerificationRepository:
    _ALLOWED_TABLES = frozenset({'verification_statuses', 'verification_types'})

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

    def create_request(self, user_id: int, verification_type_code: str):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                verification_type_id = self._id(
                    cursor, "verification_types", verification_type_code
                )
                pending_id = self._id(
                    cursor, "verification_statuses", "PENDING"
                )

                cursor.execute(
                    """
                    SELECT
                        vr.id,
                        vr.public_id,
                        vt.code AS verification_type,
                        vs.code AS status,
                        vr.submitted_at,
                        vr.reviewed_at,
                        vr.rejection_reason,
                        vr.expires_at
                    FROM verification_requests vr
                    INNER JOIN verification_types vt
                        ON vt.id = vr.verification_type_id
                    INNER JOIN verification_statuses vs
                        ON vs.id = vr.status_id
                    WHERE vr.user_id = %s
                      AND vr.verification_type_id = %s
                      AND vs.code IN ('PENDING', 'UNDER_REVIEW', 'VERIFIED')
                    ORDER BY vr.id DESC
                    LIMIT 1
                    """,
                    (user_id, verification_type_id),
                )
                existing = cursor.fetchone()
                if existing:
                    connection.commit()
                    cursor.close()
                    return existing

                public_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO verification_requests
                        (
                            public_id,
                            user_id,
                            verification_type_id,
                            status_id,
                            submitted_at
                        )
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """,
                    (
                        public_id,
                        user_id,
                        verification_type_id,
                        pending_id,
                    ),
                )
                request_id = int(cursor.lastrowid)
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return self.get_request(user_id, request_id)

    def get_request(self, user_id: int, request_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    vr.public_id,
                    vt.code AS verification_type,
                    vs.code AS status,
                    vr.submitted_at,
                    vr.reviewed_at,
                    vr.rejection_reason,
                    vr.expires_at
                FROM verification_requests vr
                INNER JOIN verification_types vt ON vt.id = vr.verification_type_id
                INNER JOIN verification_statuses vs ON vs.id = vr.status_id
                WHERE vr.id = %s
                  AND vr.user_id = %s
                LIMIT 1
                """,
                (request_id, user_id),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def add_document(self, user_id: int, request_id: int, data):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT vr.id, vs.code AS status
                    FROM verification_requests vr
                    INNER JOIN verification_statuses vs ON vs.id = vr.status_id
                    WHERE vr.id = %s
                      AND vr.user_id = %s
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (request_id, user_id),
                )
                request = cursor.fetchone()
                if not request:
                    raise ValueError("Verification request not found")

                if request["status"] not in {"PENDING", "REJECTED"}:
                    raise ValueError(
                        "Documents cannot be changed after review has started"
                    )

                document_type_id = self._id(
                    cursor,
                    "verification_document_types",
                    data.document_type_code,
                )
                document_status_id = self._id(
                    cursor,
                    "verification_statuses",
                    "PENDING",
                )

                public_id = str(uuid.uuid4())

                cursor.execute(
                    """
                    INSERT INTO verification_documents
                        (
                            public_id,
                            verification_request_id,
                            document_type_id,
                            storage_key,
                            original_filename,
                            mime_type,
                            file_size_bytes,
                            sha256_hash,
                            document_number_masked,
                            status_id
                        )
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        public_id,
                        request_id,
                        document_type_id,
                        data.storage_key,
                        data.original_filename,
                        data.mime_type,
                        data.file_size_bytes,
                        data.sha256_hash,
                        data.document_number_masked,
                        document_status_id,
                    ),
                )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return {"public_id": public_id}

    def list_requests(self, user_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    vr.public_id,
                    vt.code AS verification_type,
                    vs.code AS status,
                    vr.submitted_at,
                    vr.reviewed_at,
                    vr.rejection_reason,
                    vr.expires_at
                FROM verification_requests vr
                INNER JOIN verification_types vt ON vt.id = vr.verification_type_id
                INNER JOIN verification_statuses vs ON vs.id = vr.status_id
                WHERE vr.user_id = %s
                ORDER BY vr.created_at DESC, vr.id DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows
