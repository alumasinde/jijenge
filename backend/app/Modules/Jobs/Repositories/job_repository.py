from app.database import db_connection


class JobRepository:
    def service_exists(self, service_id: int) -> bool:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM services s
                INNER JOIN service_categories c ON c.id = s.category_id
                WHERE s.id = %s
                  AND s.is_active = 1
                  AND c.is_active = 1
                LIMIT 1
                """,
                (service_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None

    def get_status_id(self, code: str) -> int:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id FROM job_statuses WHERE code = %s AND is_active = 1 LIMIT 1",
                (code,),
            )
            row = cursor.fetchone()
            cursor.close()
            if not row:
                raise RuntimeError(f"Job status {code} is missing")
            return int(row[0])

    def create(
        self,
        customer_id: int,
        service_id: int,
        title: str,
        description: str,
        latitude: float,
        longitude: float,
        address_line: str | None,
        location_notes: str | None,
        budget_min,
        budget_max,
        preferred_start_at,
        preferred_end_at,
    ) -> dict:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                status_id = self.get_status_id("OPEN")

                cursor.execute(
                    """
                    INSERT INTO jobs
                        (
                            customer_id, service_id, status_id,
                            title, description, budget_min, budget_max,
                            preferred_start_at, preferred_end_at
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        customer_id,
                        service_id,
                        status_id,
                        title,
                        description,
                        budget_min,
                        budget_max,
                        preferred_start_at,
                        preferred_end_at,
                    ),
                )
                job_id = int(cursor.lastrowid)

                cursor.execute(
                    """
                    INSERT INTO job_locations
                        (job_id, location_point, address_line, location_notes)
                    VALUES
                        (
                            %s,
                            ST_SRID(POINT(%s, %s), 4326),
                            %s,
                            %s
                        )
                    """,
                    (
                        job_id,
                        longitude,
                        latitude,
                        address_line,
                        location_notes,
                    ),
                )

                cursor.execute(
                    """
                    INSERT INTO job_status_history
                        (job_id, status_id, changed_by_user_id, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (job_id, status_id, customer_id, "Job created"),
                )

                cursor.execute(
                    """
                    SELECT id
                    FROM worker_job_statuses
                    WHERE code = 'PENDING' AND is_active = 1
                    LIMIT 1
                    """
                )
                worker_status = cursor.fetchone()
                if not worker_status:
                    raise RuntimeError("PENDING worker status is missing")

                import json
                cursor.execute(
                    """
                    INSERT INTO worker_jobs
                        (
                            job_key, job_type, payload_json,
                            status_id, available_at
                        )
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        f"match-job:{job_id}",
                        "MATCH_JOB",
                        json.dumps({"job_id": job_id}),
                        worker_status["id"],
                    ),
                )

                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

        return self.get_by_id(job_id, customer_id)

    def get_by_id(self, job_id: int, customer_id: int) -> dict | None:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    j.id,
                    j.customer_id,
                    j.service_id,
                    s.code AS service_code,
                    s.name AS service_name,
                    js.code AS status_code,
                    j.title,
                    j.description,
                    j.budget_min,
                    j.budget_max,
                    j.preferred_start_at,
                    j.preferred_end_at,
                    ST_Y(jl.location_point) AS latitude,
                    ST_X(jl.location_point) AS longitude,
                    jl.address_line,
                    jl.location_notes,
                    j.created_at,
                    j.updated_at
                FROM jobs j
                INNER JOIN services s ON s.id = j.service_id
                INNER JOIN job_statuses js ON js.id = j.status_id
                INNER JOIN job_locations jl ON jl.job_id = j.id
                WHERE j.id = %s
                  AND j.customer_id = %s
                LIMIT 1
                """,
                (job_id, customer_id),
            )
            row = cursor.fetchone()
            cursor.close()
            return row
