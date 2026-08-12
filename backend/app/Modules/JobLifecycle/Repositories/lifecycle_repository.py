import json
from app.database import db_connection

class LifecycleRepository:
    def _status_id(self, cur, code):
        cur.execute("SELECT id FROM job_statuses WHERE code=%s AND is_active=1 LIMIT 1", (code,))
        row = cur.fetchone()
        if not row: raise RuntimeError(f"Job status {code} is missing")
        return int(row[0])

    def transition(self, job_id, user_id, role_code, target_code, notes, cancel_reason, completion_notes):
        with db_connection() as conn:
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute("""
                    SELECT j.id,j.customer_id,j.status_id,js.code status_code
                    FROM jobs j INNER JOIN job_statuses js ON js.id=j.status_id
                    WHERE j.id=%s FOR UPDATE
                """, (job_id,))
                job = cur.fetchone()
                if not job: raise LookupError("Job not found")

                assignment = None
                if role_code == "CUSTOMER":
                    if int(job["customer_id"]) != user_id: raise PermissionError("Not job owner")
                else:
                    cur.execute("""
                        SELECT ja.id,ja.provider_id
                        FROM job_assignments ja
                        WHERE ja.job_id=%s
                          AND ja.provider_id=(SELECT id FROM provider_profiles WHERE user_id=%s LIMIT 1)
                          AND ja.cancelled_at IS NULL
                        LIMIT 1 FOR UPDATE
                    """, (job_id, user_id))
                    assignment = cur.fetchone()
                    if not assignment: raise PermissionError("No active provider assignment")

                cur.execute("""
                    SELECT t.requires_assignment
                    FROM job_status_transitions t
                    INNER JOIN job_statuses ts ON ts.id=t.to_status_id
                    WHERE t.from_status_id=%s AND ts.code=%s
                      AND t.actor_role_code=%s AND t.is_active=1 LIMIT 1
                """, (job["status_id"], target_code, role_code))
                rule = cur.fetchone()
                if not rule: raise ValueError(f"Invalid transition from {job['status_code']} to {target_code}")
                if rule["requires_assignment"] and not assignment: raise PermissionError("Assignment required")

                target_id = self._status_id(cur, target_code)
                detail = cancel_reason or completion_notes or notes

                if target_code == "CANCELLED":
                    cur.execute("UPDATE jobs SET status_id=%s,cancelled_at=CURRENT_TIMESTAMP,cancellation_reason=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s", (target_id, detail, job_id))
                    cur.execute("UPDATE job_assignments SET cancelled_at=CURRENT_TIMESTAMP,cancellation_reason=%s WHERE job_id=%s AND cancelled_at IS NULL", (detail, job_id))
                elif target_code == "IN_PROGRESS":
                    cur.execute("UPDATE jobs SET status_id=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s", (target_id, job_id))
                    cur.execute("UPDATE job_assignments SET started_at=COALESCE(started_at,CURRENT_TIMESTAMP) WHERE job_id=%s AND cancelled_at IS NULL", (job_id,))
                elif target_code == "COMPLETED":
                    cur.execute("UPDATE jobs SET status_id=%s,completed_at=CURRENT_TIMESTAMP,completion_notes=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s", (target_id, completion_notes or notes, job_id))
                    cur.execute("UPDATE job_assignments SET completed_at=CURRENT_TIMESTAMP WHERE job_id=%s AND cancelled_at IS NULL", (job_id,))
                else:
                    cur.execute("UPDATE jobs SET status_id=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s", (target_id, job_id))

                cur.execute("INSERT INTO job_status_history (job_id,status_id,changed_by_user_id,notes) VALUES (%s,%s,%s,%s)", (job_id,target_id,user_id,detail))
                event = {"CANCELLED":"JOB_CANCELLED","ON_THE_WAY":"PROVIDER_ON_THE_WAY","IN_PROGRESS":"JOB_STARTED","COMPLETED":"JOB_COMPLETED"}.get(target_code,"JOB_STATUS_CHANGED")
                cur.execute("INSERT INTO job_events (job_id,event_type,actor_user_id,from_status_id,to_status_id,metadata_json,notes) VALUES (%s,%s,%s,%s,%s,%s,%s)", (job_id,event,user_id,job["status_id"],target_id,json.dumps({"actor_role":role_code}),detail))
                conn.commit()
            except Exception:
                conn.rollback(); raise
            finally: cur.close()
        return self.lifecycle(job_id)

    def lifecycle(self, job_id):
        with db_connection() as conn:
            cur=conn.cursor(dictionary=True)
            cur.execute("""
                SELECT j.id job_id,js.code status_code,ja.provider_id assigned_provider_id,ja.assigned_at,ja.started_at,
                       j.completed_at,j.cancelled_at,j.cancellation_reason,j.completion_notes
                FROM jobs j INNER JOIN job_statuses js ON js.id=j.status_id
                LEFT JOIN job_assignments ja ON ja.job_id=j.id
                WHERE j.id=%s LIMIT 1
            """, (job_id,))
            row=cur.fetchone();cur.close();return row

    def events(self, job_id, user_id, role_code):
        with db_connection() as conn:
            cur=conn.cursor(dictionary=True)
            if role_code == "CUSTOMER":
                cur.execute("SELECT 1 FROM jobs WHERE id=%s AND customer_id=%s LIMIT 1", (job_id,user_id))
            else:
                cur.execute("SELECT 1 FROM job_assignments WHERE job_id=%s AND provider_id=(SELECT id FROM provider_profiles WHERE user_id=%s LIMIT 1) AND cancelled_at IS NULL LIMIT 1", (job_id,user_id))
            if not cur.fetchone(): cur.close(); raise LookupError("Job not found")
            cur.execute("""
                SELECT e.id,e.job_id,e.event_type,e.actor_user_id,fs.code from_status,ts.code to_status,e.notes,e.created_at
                FROM job_events e LEFT JOIN job_statuses fs ON fs.id=e.from_status_id LEFT JOIN job_statuses ts ON ts.id=e.to_status_id
                WHERE e.job_id=%s ORDER BY e.created_at ASC,e.id ASC
            """, (job_id,))
            rows=cur.fetchall();cur.close();return rows
