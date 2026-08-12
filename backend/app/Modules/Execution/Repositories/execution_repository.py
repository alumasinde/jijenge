from app.database import db_connection


class ExecutionRepository:
    def _status_id(self, cursor, code):
        cursor.execute(
            "SELECT id FROM job_execution_statuses WHERE code = %s AND is_active = 1 LIMIT 1",
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Execution status {code} is missing")
        return int(row["id"])

    def _event_id(self, cursor, code):
        cursor.execute(
            "SELECT id FROM job_execution_event_types WHERE code = %s AND is_active = 1 LIMIT 1",
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Execution event {code} is missing")
        return int(row["id"])

    def _get_assignment_locked(self, cursor, assignment_id):
        cursor.execute(
            """
            SELECT
                ja.*,
                ast.code AS assignment_status,
                jes.code AS execution_status,
                j.customer_id
            FROM job_assignments ja
            INNER JOIN assignment_statuses ast ON ast.id = ja.status_id
            INNER JOIN job_execution_statuses jes ON jes.id = ja.execution_status_id
            INNER JOIN jobs j ON j.id = ja.job_id
            WHERE ja.id = %s
            FOR UPDATE
            """,
            (assignment_id,),
        )
        return cursor.fetchone()

    def _add_event(self, cursor, assignment_id, code, actor_user_id, location, notes):
        event_id = self._event_id(cursor, code)
        lat = location.latitude if location else None
        lon = location.longitude if location else None
        cursor.execute(
            """
            INSERT INTO job_execution_events
                (
                    assignment_id, event_type_id, actor_user_id,
                    latitude, longitude, notes
                )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (assignment_id, event_id, actor_user_id, lat, lon, notes),
        )

    def get_for_provider(self, assignment_id, provider_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ja.id AS assignment_id,
                    ja.job_id,
                    jes.code AS status,
                    ja.assigned_at,
                    ja.confirmed_at,
                    ja.started_at,
                    ja.completed_at,
                    ja.customer_confirmation_deadline
                FROM job_assignments ja
                INNER JOIN job_execution_statuses jes
                    ON jes.id = ja.execution_status_id
                WHERE ja.id = %s AND ja.provider_id = %s
                LIMIT 1
                """,
                (assignment_id, provider_id),
            )
            row = cursor.fetchone()
            cursor.close()
        return row

    def get_for_customer(self, assignment_id, customer_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ja.id AS assignment_id,
                    ja.job_id,
                    jes.code AS status,
                    ja.assigned_at,
                    ja.confirmed_at,
                    ja.started_at,
                    ja.completed_at,
                    ja.customer_confirmation_deadline
                FROM job_assignments ja
                INNER JOIN job_execution_statuses jes
                    ON jes.id = ja.execution_status_id
                WHERE ja.id = %s AND ja.assigned_by_user_id = %s
                LIMIT 1
                """,
                (assignment_id, customer_id),
            )
            row = cursor.fetchone()
            cursor.close()
        return row

    def transition_provider(self, assignment_id, provider_id, target, event, location, notes):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                row = self._get_assignment_locked(cursor, assignment_id)
                if not row or int(row["provider_id"]) != provider_id:
                    raise ValueError("Assignment not found")

                allowed = {
                    "ON_THE_WAY": {"CONFIRMED"},
                    "ARRIVED": {"ON_THE_WAY"},
                    "IN_PROGRESS": {"ARRIVED", "PAUSED"},
                    "PAUSED": {"IN_PROGRESS"},
                }
                if target not in allowed or row["execution_status"] not in allowed[target]:
                    raise ValueError(
                        f"Cannot move assignment from {row['execution_status']} to {target}"
                    )

                status_id = self._status_id(cursor, target)
                started = target == "IN_PROGRESS" and row["started_at"] is None
                cursor.execute(
                    """
                    UPDATE job_assignments
                    SET execution_status_id = %s,
                        started_at = CASE
                            WHEN %s = 1 THEN CURRENT_TIMESTAMP
                            ELSE started_at
                        END
                    WHERE id = %s
                    """,
                    (status_id, int(started), assignment_id),
                )
                self._add_event(
                    cursor, assignment_id, event, provider_id, location, notes
                )
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
        return self.get_for_provider(assignment_id, provider_id)

    def submit_completion(self, assignment_id, provider_id, notes):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                row = self._get_assignment_locked(cursor, assignment_id)
                if not row or int(row["provider_id"]) != provider_id:
                    raise ValueError("Assignment not found")
                if row["execution_status"] not in {"IN_PROGRESS", "PAUSED"}:
                    raise ValueError("Job cannot be completed from its current state")

                status_id = self._status_id(cursor, "COMPLETED_PENDING_CONFIRMATION")
                cursor.execute(
                    """
                    UPDATE job_assignments
                    SET execution_status_id = %s,
                        completed_at = CURRENT_TIMESTAMP,
                        customer_confirmation_deadline =
                            DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 24 HOUR)
                    WHERE id = %s
                    """,
                    (status_id, assignment_id),
                )
                self._add_event(
                    cursor, assignment_id, "COMPLETION_SUBMITTED",
                    provider_id, None, notes
                )
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
        return self.get_for_provider(assignment_id, provider_id)

    def confirm_completion(self, assignment_id, customer_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                row = self._get_assignment_locked(cursor, assignment_id)
                if not row or int(row["customer_id"]) != customer_id:
                    raise ValueError("Assignment not found")
                if row["execution_status"] != "COMPLETED_PENDING_CONFIRMATION":
                    raise ValueError("Completion is not awaiting confirmation")

                status_id = self._status_id(cursor, "COMPLETED")
                cursor.execute(
                    """
                    UPDATE job_assignments
                    SET execution_status_id = %s
                    WHERE id = %s
                    """,
                    (status_id, assignment_id),
                )
                self._add_event(
                    cursor, assignment_id, "CUSTOMER_CONFIRMED",
                    customer_id, None, "Customer confirmed completion"
                )
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
        return self.get_for_customer(assignment_id, customer_id)

    def open_dispute(self, assignment_id, customer_id, dispute_type, description):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                row = self._get_assignment_locked(cursor, assignment_id)
                if not row or int(row["customer_id"]) != customer_id:
                    raise ValueError("Assignment not found")
                if row["execution_status"] not in {
                    "COMPLETED_PENDING_CONFIRMATION", "COMPLETED"
                }:
                    raise ValueError("A dispute can only be opened after completion is submitted")

                cursor.execute(
                    "SELECT id FROM dispute_types WHERE code = %s AND is_active = 1 LIMIT 1",
                    (dispute_type,),
                )
                dtype = cursor.fetchone()
                if not dtype:
                    raise ValueError("Invalid dispute type")

                cursor.execute(
                    "SELECT id FROM dispute_statuses WHERE code = 'OPEN' LIMIT 1"
                )
                dstatus = cursor.fetchone()

                cursor.execute(
                    """
                    INSERT INTO job_disputes
                        (
                            assignment_id, opened_by_user_id,
                            dispute_type_id, status_id, description
                        )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        assignment_id, customer_id,
                        dtype["id"], dstatus["id"], description,
                    ),
                )

                execution_status = self._status_id(cursor, "DISPUTED")
                cursor.execute(
                    """
                    UPDATE job_assignments
                    SET execution_status_id = %s
                    WHERE id = %s
                    """,
                    (execution_status, assignment_id),
                )
                self._add_event(
                    cursor, assignment_id, "DISPUTED",
                    customer_id, None, description
                )
                connection.commit()
                dispute_id = cursor.lastrowid
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
        return dispute_id
