import uuid

from app.database import db_connection


class ReviewRepository:
    _ALLOWED_TABLES = frozenset({'review_directions', 'review_statuses'})

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

    def get_review_context(self, job_id: int, reviewer_user_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    j.id AS job_id,
                    j.customer_id,
                    js.code AS job_status,
                    ja.provider_id,
                    pp.user_id AS provider_user_id
                FROM jobs j
                INNER JOIN job_statuses js ON js.id = j.status_id
                LEFT JOIN job_assignments ja ON ja.job_id = j.id
                LEFT JOIN provider_profiles pp ON pp.id = ja.provider_id
                WHERE j.id = %s
                LIMIT 1
                """,
                (job_id,),
            )
            row = cursor.fetchone()
            cursor.close()

        if not row:
            return None

        if reviewer_user_id == row["customer_id"]:
            return {
                **row,
                "direction_code": "CUSTOMER_TO_PROVIDER",
                "reviewee_user_id": row["provider_user_id"],
                "reviewer_type": "CUSTOMER",
            }

        if reviewer_user_id == row["provider_user_id"]:
            return {
                **row,
                "direction_code": "PROVIDER_TO_CUSTOMER",
                "reviewee_user_id": row["customer_id"],
                "reviewer_type": "PROVIDER",
            }

        return None

    def create(
        self,
        *,
        job_id,
        reviewer_user_id,
        reviewee_user_id,
        direction_code,
        overall_rating,
        title,
        body,
        dimension_scores,
    ):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                direction_id = self._id(
                    cursor, "review_directions", direction_code
                )
                status_id = self._id(
                    cursor, "review_statuses", "PUBLISHED"
                )

                public_id = str(uuid.uuid4())

                cursor.execute(
                    """
                    INSERT INTO reviews
                        (
                            public_id,
                            job_id,
                            reviewer_user_id,
                            reviewee_user_id,
                            direction_id,
                            status_id,
                            title,
                            body,
                            overall_rating,
                            published_at
                        )
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """,
                    (
                        public_id,
                        job_id,
                        reviewer_user_id,
                        reviewee_user_id,
                        direction_id,
                        status_id,
                        title,
                        body,
                        overall_rating,
                    ),
                )
                review_id = int(cursor.lastrowid)

                for dimension_code, score in dimension_scores.items():
                    cursor.execute(
                        """
                        SELECT id
                        FROM review_rating_dimensions
                        WHERE code = %s
                          AND is_active = 1
                        LIMIT 1
                        """,
                        (dimension_code,),
                    )
                    dimension = cursor.fetchone()
                    if not dimension:
                        raise ValueError(
                            f"Unknown rating dimension: {dimension_code}"
                        )

                    cursor.execute(
                        """
                        INSERT INTO review_dimension_scores
                            (review_id, dimension_id, score)
                        VALUES (%s, %s, %s)
                        """,
                        (review_id, dimension["id"], score),
                    )

                self.refresh_provider_summary(
                    cursor, reviewee_user_id
                )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return self.get_by_id(review_id)

    def refresh_provider_summary(self, cursor, provider_user_id: int):
        cursor.execute(
            """
            INSERT INTO provider_rating_summaries
                (
                    provider_user_id,
                    published_review_count,
                    overall_rating_sum,
                    overall_rating_average
                )
            SELECT
                %s,
                COUNT(*),
                COALESCE(SUM(overall_rating), 0),
                ROUND(AVG(overall_rating), 2)
            FROM reviews r
            INNER JOIN review_statuses rs ON rs.id = r.status_id
            WHERE r.reviewee_user_id = %s
              AND rs.code = 'PUBLISHED'
            ON DUPLICATE KEY UPDATE
                published_review_count = VALUES(published_review_count),
                overall_rating_sum = VALUES(overall_rating_sum),
                overall_rating_average = VALUES(overall_rating_average)
            """,
            (provider_user_id, provider_user_id),
        )

        dimension_map = {
            "quality_average": "QUALITY",
            "communication_average": "COMMUNICATION",
            "punctuality_average": "PUNCTUALITY",
            "professionalism_average": "PROFESSIONALISM",
        }

        updates = {}
        for column, code in dimension_map.items():
            cursor.execute(
                """
                SELECT ROUND(AVG(rds.score), 2) AS average_score
                FROM review_dimension_scores rds
                INNER JOIN reviews r ON r.id = rds.review_id
                INNER JOIN review_statuses rs ON rs.id = r.status_id
                INNER JOIN review_rating_dimensions rrd
                    ON rrd.id = rds.dimension_id
                WHERE r.reviewee_user_id = %s
                  AND rs.code = 'PUBLISHED'
                  AND rrd.code = %s
                """,
                (provider_user_id, code),
            )
            updates[column] = cursor.fetchone()["average_score"]

        cursor.execute(
            """
            UPDATE provider_rating_summaries
            SET quality_average = %s,
                communication_average = %s,
                punctuality_average = %s,
                professionalism_average = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE provider_user_id = %s
            """,
            (
                updates["quality_average"],
                updates["communication_average"],
                updates["punctuality_average"],
                updates["professionalism_average"],
                provider_user_id,
            ),
        )

    def get_by_id(self, review_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    r.public_id,
                    r.job_id,
                    r.reviewer_user_id,
                    r.reviewee_user_id,
                    rd.code AS direction,
                    rs.code AS status,
                    r.overall_rating,
                    r.title,
                    r.body,
                    r.created_at
                FROM reviews r
                INNER JOIN review_directions rd ON rd.id = r.direction_id
                INNER JOIN review_statuses rs ON rs.id = r.status_id
                WHERE r.id = %s
                LIMIT 1
                """,
                (review_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def list_for_user(self, user_id: int, limit: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    r.public_id,
                    r.job_id,
                    r.reviewer_user_id,
                    r.reviewee_user_id,
                    rd.code AS direction,
                    rs.code AS status,
                    r.overall_rating,
                    r.title,
                    r.body,
                    r.created_at
                FROM reviews r
                INNER JOIN review_directions rd ON rd.id = r.direction_id
                INNER JOIN review_statuses rs ON rs.id = r.status_id
                WHERE r.reviewee_user_id = %s
                  AND rs.code = 'PUBLISHED'
                ORDER BY r.created_at DESC, r.id DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def provider_summary(self, provider_user_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    provider_user_id,
                    published_review_count,
                    overall_rating_average,
                    quality_average,
                    communication_average,
                    punctuality_average,
                    professionalism_average
                FROM provider_rating_summaries
                WHERE provider_user_id = %s
                LIMIT 1
                """,
                (provider_user_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row
