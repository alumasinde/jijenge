from app.database import db_connection


class ApplicationRepository:
    def provider_profile_for_user(self, user_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, provider_status_id FROM provider_profiles WHERE user_id = %s LIMIT 1",
                (user_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def get_provider_status_code(self, provider_id: int):
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT ps.code
                FROM provider_profiles pp
                INNER JOIN provider_statuses ps ON ps.id = pp.provider_status_id
                WHERE pp.id = %s
                LIMIT 1
                """,
                (provider_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row[0] if row else None

    def get_job_for_application(self, job_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    j.id, j.customer_id, j.service_id, js.code AS status_code
                FROM jobs j
                INNER JOIN job_statuses js ON js.id = j.status_id
                WHERE j.id = %s
                LIMIT 1
                """,
                (job_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row


    def provider_can_reach_job(self, provider_id: int, job_id: int) -> bool:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ST_Y(jl.location_point) AS latitude,
                    ST_X(jl.location_point) AS longitude
                FROM jobs j
                INNER JOIN job_locations jl ON jl.job_id = j.id
                WHERE j.id = %s
                LIMIT 1
                """,
                (job_id,),
            )
            job = cursor.fetchone()
            if not job:
                cursor.close()
                return False

            cursor.execute(
                """
                SELECT
                    pmp.max_distance_km,
                    ST_Distance_Sphere(
                        pl.location_point,
                        ST_SRID(POINT(%s, %s), 4326)
                    ) / 1000 AS distance_km
                FROM provider_matching_preferences pmp
                INNER JOIN provider_locations pl
                    ON pl.provider_id = pmp.provider_id
                   AND pl.is_active = 1
                   AND pl.is_primary = 1
                WHERE pmp.provider_id = %s
                LIMIT 1
                """,
                (
                    job["longitude"], job["latitude"],
                    provider_id,
                ),
            )
            preference = cursor.fetchone()

            if preference and float(preference["distance_km"]) <= float(
                preference["max_distance_km"]
            ):
                cursor.close()
                return True

            cursor.execute(
                """
                SELECT 1
                FROM provider_service_areas psa
                WHERE psa.provider_id = %s
                  AND psa.is_active = 1
                  AND ST_Distance_Sphere(
                      psa.center_point,
                      ST_SRID(POINT(%s, %s), 4326)
                  ) <= psa.radius_km * 1000
                LIMIT 1
                """,
                (
                    provider_id,
                    job["longitude"], job["latitude"],
                ),
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None

    def provider_offers_service(self, provider_id: int, service_id: int) -> bool:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM provider_services
                WHERE provider_id = %s
                  AND service_id = %s
                  AND is_active = 1
                LIMIT 1
                """,
                (provider_id, service_id),
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None

    def get_application(self, application_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ja.id, ja.job_id, ja.provider_id,
                    jas.code AS status_code,
                    ja.proposed_price, ja.message,
                    ja.estimated_start_at,
                    ja.created_at, ja.updated_at, ja.responded_at
                FROM job_applications ja
                INNER JOIN job_application_statuses jas ON jas.id = ja.status_id
                WHERE ja.id = %s
                LIMIT 1
                """,
                (application_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def create_application(
        self, job_id, provider_id, proposed_price, message, estimated_start_at
    ):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT id FROM job_application_statuses WHERE code = 'PENDING' AND is_active = 1 LIMIT 1"
                )
                status = cursor.fetchone()
                if not status:
                    raise RuntimeError("PENDING application status is missing")

                cursor.execute(
                    """
                    INSERT INTO job_applications
                        (
                            job_id, provider_id, status_id,
                            proposed_price, message, estimated_start_at
                        )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        job_id, provider_id, status["id"],
                        proposed_price, message, estimated_start_at,
                    ),
                )
                application_id = cursor.lastrowid
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
        return self.get_application(int(application_id))

    def list_for_job(self, job_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ja.id, ja.job_id, ja.provider_id,
                    jas.code AS status_code,
                    ja.proposed_price, ja.message,
                    ja.estimated_start_at,
                    ja.created_at, ja.updated_at, ja.responded_at
                FROM job_applications ja
                INNER JOIN job_application_statuses jas ON jas.id = ja.status_id
                WHERE ja.job_id = %s
                ORDER BY ja.created_at ASC, ja.id ASC
                """,
                (job_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def list_for_provider(self, provider_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ja.id, ja.job_id, ja.provider_id,
                    jas.code AS status_code,
                    ja.proposed_price, ja.message,
                    ja.estimated_start_at,
                    ja.created_at, ja.updated_at, ja.responded_at
                FROM job_applications ja
                INNER JOIN job_application_statuses jas ON jas.id = ja.status_id
                WHERE ja.provider_id = %s
                ORDER BY ja.created_at DESC, ja.id DESC
                """,
                (provider_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def get_application_for_provider(self, application_id: int, provider_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ja.id, ja.job_id, ja.provider_id,
                    jas.code AS status_code,
                    ja.proposed_price, ja.message,
                    ja.estimated_start_at,
                    ja.created_at, ja.updated_at, ja.responded_at
                FROM job_applications ja
                INNER JOIN job_application_statuses jas ON jas.id = ja.status_id
                WHERE ja.id = %s
                  AND ja.provider_id = %s
                LIMIT 1
                """,
                (application_id, provider_id),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def withdraw(self, application_id: int, provider_id: int):
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE job_applications ja
                INNER JOIN job_application_statuses jas
                    ON jas.code = 'WITHDRAWN'
                SET ja.status_id = jas.id,
                    ja.responded_at = CURRENT_TIMESTAMP
                WHERE ja.id = %s
                  AND ja.provider_id = %s
                  AND ja.status_id = (
                      SELECT id FROM job_application_statuses
                      WHERE code = 'PENDING' LIMIT 1
                  )
                """,
                (application_id, provider_id),
            )
            connection.commit()
            cursor.close()
        return self.get_application_for_provider(application_id, provider_id)


    def accept_and_assign(self, application_id: int, customer_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()

                cursor.execute(
                    """
                    SELECT
                        ja.id, ja.job_id, ja.provider_id,
                        j.customer_id, js.code AS job_status_code,
                        ja.status_id AS application_status_id
                    FROM job_applications ja
                    INNER JOIN jobs j ON j.id = ja.job_id
                    INNER JOIN job_statuses js ON js.id = j.status_id
                    WHERE ja.id = %s
                    FOR UPDATE
                    """,
                    (application_id,),
                )
                application = cursor.fetchone()

                if not application:
                    raise ValueError("Application not found")
                if int(application["customer_id"]) != customer_id:
                    raise PermissionError("Application does not belong to this customer")
                if application["job_status_code"] != "OPEN":
                    raise ValueError("Job is no longer open")

                cursor.execute(
                    """
                    SELECT code
                    FROM job_application_statuses
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (application["application_status_id"],),
                )
                app_status = cursor.fetchone()
                if not app_status or app_status["code"] != "PENDING":
                    raise ValueError("Application is no longer pending")

                # Lock the single job row. The UNIQUE(job_id) assignment constraint
                # is the final database-level protection against double assignment.
                cursor.execute(
                    """
                    SELECT id
                    FROM job_assignments
                    WHERE job_id = %s
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (application["job_id"],),
                )
                if cursor.fetchone():
                    raise ValueError("Job already has an assignment")

                cursor.execute(
                    "SELECT id FROM job_statuses WHERE code = 'ASSIGNED' LIMIT 1"
                )
                assigned_status = cursor.fetchone()

                cursor.execute(
                    "SELECT id FROM job_application_statuses WHERE code = 'ACCEPTED' LIMIT 1"
                )
                accepted_status = cursor.fetchone()

                cursor.execute(
                    "SELECT id FROM job_application_statuses WHERE code = 'CANCELLED' LIMIT 1"
                )
                cancelled_status = cursor.fetchone()

                cursor.execute(
                    "SELECT id FROM assignment_statuses WHERE code = 'PENDING_PROVIDER_CONFIRMATION' LIMIT 1"
                )
                pending_assignment_status = cursor.fetchone()

                if not all((assigned_status, accepted_status, cancelled_status, pending_assignment_status)):
                    raise RuntimeError("Assignment statuses are not configured")

                cursor.execute(
                    """
                    UPDATE job_applications
                    SET status_id = %s,
                        responded_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (accepted_status["id"], application_id),
                )

                cursor.execute(
                    """
                    INSERT INTO job_assignments
                        (
                            job_id, provider_id, application_id,
                            status_id, assigned_by_user_id,
                            confirmation_deadline
                        )
                    VALUES
                        (
                            %s, %s, %s, %s, %s,
                            DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 30 MINUTE)
                        )
                    """,
                    (
                        application["job_id"],
                        application["provider_id"],
                        application_id,
                        pending_assignment_status["id"],
                        customer_id,
                    ),
                )
                assignment_id = int(cursor.lastrowid)

                cursor.execute(
                    """
                    UPDATE job_applications
                    SET status_id = %s,
                        responded_at = CURRENT_TIMESTAMP
                    WHERE job_id = %s
                      AND id <> %s
                      AND status_id = (
                          SELECT id FROM job_application_statuses
                          WHERE code = 'PENDING' LIMIT 1
                      )
                    """,
                    (
                        cancelled_status["id"],
                        application["job_id"],
                        application_id,
                    ),
                )

                cursor.execute(
                    """
                    UPDATE jobs
                    SET status_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND status_id = (
                          SELECT id FROM job_statuses
                          WHERE code = 'OPEN' LIMIT 1
                      )
                    """,
                    (assigned_status["id"], application["job_id"]),
                )

                cursor.execute(
                    """
                    INSERT INTO job_status_history
                        (job_id, status_id, changed_by_user_id, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        application["job_id"],
                        assigned_status["id"],
                        customer_id,
                        "Provider selected; awaiting provider confirmation",
                    ),
                )

                cursor.execute(
                    "SELECT id FROM assignment_event_types WHERE code = 'ASSIGNED' LIMIT 1"
                )
                event_type = cursor.fetchone()
                cursor.execute(
                    """
                    INSERT INTO job_assignment_events
                        (assignment_id, event_type_id, actor_user_id, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        assignment_id,
                        event_type["id"],
                        customer_id,
                        "Provider selected by customer",
                    ),
                )

                cursor.execute(
                    "SELECT id FROM assignment_dispatch_statuses WHERE code = 'PENDING' LIMIT 1"
                )
                dispatch_status = cursor.fetchone()
                cursor.execute(
                    """
                    INSERT INTO assignment_dispatches
                        (
                            assignment_id, status_id,
                            expires_at
                        )
                    VALUES
                        (
                            %s, %s,
                            DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 30 MINUTE)
                        )
                    """,
                    (assignment_id, dispatch_status["id"]),
                )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return self.get_assignment(int(assignment_id), customer_id)

    def get_assignment(self, assignment_id: int, customer_id: int | None = None):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT
                    ja.id, ja.job_id, ja.provider_id, ja.application_id,
                    ass.code AS status_code,
                    ja.assigned_by_user_id, ja.assigned_at,
                    ja.confirmation_deadline, ja.confirmed_at,
                    ja.declined_at, ja.decline_reason,
                    ja.started_at, ja.completed_at, ja.cancelled_at
                FROM job_assignments ja
                INNER JOIN assignment_statuses ass
                    ON ass.id = ja.status_id
                WHERE ja.id = %s
            """
            params = [assignment_id]
            if customer_id is not None:
                query += " AND ja.assigned_by_user_id = %s"
                params.append(customer_id)
            query += " LIMIT 1"
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            return row

    def get_assignment_for_provider(self, assignment_id: int, provider_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ja.id, ja.job_id, ja.provider_id, ja.application_id,
                    ass.code AS status_code,
                    ja.assigned_by_user_id, ja.assigned_at,
                    ja.confirmation_deadline, ja.confirmed_at,
                    ja.declined_at, ja.decline_reason,
                    ja.started_at, ja.completed_at, ja.cancelled_at
                FROM job_assignments ja
                INNER JOIN assignment_statuses ass
                    ON ass.id = ja.status_id
                WHERE ja.id = %s
                  AND ja.provider_id = %s
                LIMIT 1
                """,
                (assignment_id, provider_id),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def _assignment_status_id(self, cursor, code):
        cursor.execute(
            "SELECT id FROM assignment_statuses WHERE code = %s AND is_active = 1 LIMIT 1",
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Assignment status {code} is missing")
        return int(row["id"])

    def _assignment_event_id(self, cursor, code):
        cursor.execute(
            "SELECT id FROM assignment_event_types WHERE code = %s AND is_active = 1 LIMIT 1",
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Assignment event {code} is missing")
        return int(row["id"])

    def confirm_assignment(self, assignment_id: int, provider_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT
                        ja.*,
                        ass.code AS status_code
                    FROM job_assignments ja
                    INNER JOIN assignment_statuses ass ON ass.id = ja.status_id
                    WHERE ja.id = %s
                      AND ja.provider_id = %s
                    FOR UPDATE
                    """,
                    (assignment_id, provider_id),
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Assignment not found")
                if row["status_code"] != "PENDING_PROVIDER_CONFIRMATION":
                    raise ValueError("Assignment is no longer awaiting confirmation")
                if row["confirmation_deadline"] and row["confirmation_deadline"] <= __import__("datetime").datetime.now():
                    raise ValueError("Assignment confirmation has expired")

                confirmed_id = self._assignment_status_id(cursor, "CONFIRMED")
                event_id = self._assignment_event_id(cursor, "CONFIRMED")

                cursor.execute(
                    """
                    UPDATE job_assignments
                    SET status_id = %s,
                        confirmed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (confirmed_id, assignment_id),
                )
                cursor.execute(
                    """
                    INSERT INTO job_assignment_events
                        (assignment_id, event_type_id, actor_user_id, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (assignment_id, event_id, None, "Provider confirmed assignment"),
                )

                cursor.execute(
                    """
                    INSERT INTO notifications
                        (
                            recipient_user_id,
                            notification_type_id,
                            title, body,
                            entity_type, entity_id, data_json
                        )
                    SELECT
                        ja.assigned_by_user_id,
                        nt.id,
                        'Assignment confirmed',
                        'The selected provider confirmed the job assignment.',
                        'ASSIGNMENT',
                        ja.id,
                        JSON_OBJECT('assignment_id', ja.id, 'job_id', ja.job_id)
                    FROM job_assignments ja
                    INNER JOIN notification_types nt
                        ON nt.code = 'ASSIGNMENT_CONFIRMED'
                    WHERE ja.id = %s
                    """,
                    (assignment_id,),
                )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return self.get_assignment_for_provider(assignment_id, provider_id)

    def decline_assignment(self, assignment_id: int, provider_id: int, reason: str | None):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT ja.*, ass.code AS status_code
                    FROM job_assignments ja
                    INNER JOIN assignment_statuses ass ON ass.id = ja.status_id
                    WHERE ja.id = %s
                      AND ja.provider_id = %s
                    FOR UPDATE
                    """,
                    (assignment_id, provider_id),
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Assignment not found")
                if row["status_code"] != "PENDING_PROVIDER_CONFIRMATION":
                    raise ValueError("Assignment is no longer awaiting confirmation")

                cancelled_id = self._assignment_status_id(cursor, "PROVIDER_DECLINED")
                event_id = self._assignment_event_id(cursor, "DECLINED")
                open_status = self._job_status_id(cursor, "OPEN")
                cursor.execute(
                    """
                    UPDATE job_assignments
                    SET status_id = %s,
                        declined_at = CURRENT_TIMESTAMP,
                        decline_reason = %s
                    WHERE id = %s
                    """,
                    (cancelled_id, reason, assignment_id),
                )

                cursor.execute(
                    """
                    UPDATE jobs
                    SET status_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND status_id = (
                          SELECT id FROM job_statuses WHERE code = 'ASSIGNED' LIMIT 1
                      )
                    """,
                    (open_status, row["job_id"]),
                )

                cursor.execute(
                    """
                    INSERT INTO job_assignment_events
                        (assignment_id, event_type_id, actor_user_id, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (assignment_id, event_id, None, reason or "Provider declined assignment"),
                )

                cursor.execute(
                    """
                    INSERT INTO notifications
                        (
                            recipient_user_id,
                            notification_type_id,
                            title, body,
                            entity_type, entity_id, data_json
                        )
                    SELECT
                        ja.assigned_by_user_id,
                        nt.id,
                        'Assignment declined',
                        'The selected provider declined the assignment.',
                        'ASSIGNMENT',
                        ja.id,
                        JSON_OBJECT('assignment_id', ja.id, 'job_id', ja.job_id)
                    FROM job_assignments ja
                    INNER JOIN notification_types nt
                        ON nt.code = 'ASSIGNMENT_DECLINED'
                    WHERE ja.id = %s
                    """,
                    (assignment_id,),
                )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
        return self.get_assignment_for_provider(assignment_id, provider_id)

    def _job_status_id(self, cursor, code):
        cursor.execute(
            "SELECT id FROM job_statuses WHERE code = %s AND is_active = 1 LIMIT 1",
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Job status {code} is missing")
        return int(row["id"])

    def get_assignment(self, assignment_id: int, customer_id: int | None = None):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT
                    id, job_id, provider_id, application_id,
                    assigned_by_user_id, assigned_at
                FROM job_assignments
                WHERE id = %s
            """
            params = [assignment_id]
            if customer_id is not None:
                query += " AND assigned_by_user_id = %s"
                params.append(customer_id)
            query += " LIMIT 1"
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            return row
