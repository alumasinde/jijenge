from __future__ import annotations

import argparse
import json
import os
import socket
import time
from datetime import timedelta

from app.database import db_connection
from app.Modules.Matching.Services.matching_service import MatchingService


class Worker:
    def __init__(self):
        self.worker_id = f"{socket.gethostname()}:{os.getpid()}"
        self.matching = MatchingService()

    def claim(self):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT
                        wj.id,
                        wj.job_type,
                        wj.payload_json,
                        wj.attempt_count,
                        wj.max_attempts
                    FROM worker_jobs wj
                    INNER JOIN worker_job_statuses wjs
                        ON wjs.id = wj.status_id
                    WHERE wjs.code = 'PENDING'
                      AND wj.available_at <= CURRENT_TIMESTAMP
                    ORDER BY wj.id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                    """
                )
                row = cursor.fetchone()
                if not row:
                    connection.rollback()
                    return None

                cursor.execute(
                    "SELECT id FROM worker_job_statuses WHERE code = 'PROCESSING' LIMIT 1"
                )
                processing = cursor.fetchone()
                cursor.execute(
                    """
                    UPDATE worker_jobs
                    SET status_id = %s,
                        locked_at = CURRENT_TIMESTAMP,
                        locked_by = %s,
                        attempt_count = attempt_count + 1
                    WHERE id = %s
                    """,
                    (processing["id"], self.worker_id, row["id"]),
                )
                connection.commit()
                return row
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def finish(self, job_id, success, error=None):
        with db_connection() as connection:
            cursor = connection.cursor()
            if success:
                cursor.execute(
                    "SELECT id FROM worker_job_statuses WHERE code = 'SUCCEEDED' LIMIT 1"
                )
                status_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    UPDATE worker_jobs
                    SET status_id = %s,
                        succeeded_at = CURRENT_TIMESTAMP,
                        locked_at = NULL,
                        locked_by = NULL,
                        last_error = NULL
                    WHERE id = %s
                    """,
                    (status_id, job_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT attempt_count, max_attempts
                    FROM worker_jobs
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (job_id,),
                )
                row = cursor.fetchone()
                target = "DEAD_LETTER" if row[0] >= row[1] else "PENDING"
                cursor.execute(
                    "SELECT id FROM worker_job_statuses WHERE code = %s LIMIT 1",
                    (target,),
                )
                status_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    UPDATE worker_jobs
                    SET status_id = %s,
                        available_at = DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 1 MINUTE),
                        locked_at = NULL,
                        locked_by = NULL,
                        last_error = %s
                    WHERE id = %s
                    """,
                    (status_id, str(error)[:2000], job_id),
                )
            connection.commit()
            cursor.close()


    def expire_assignments(self):
        from app.database import db_connection
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT
                        ja.id, ja.job_id, ja.provider_id
                    FROM job_assignments ja
                    INNER JOIN assignment_statuses ass
                        ON ass.id = ja.status_id
                    WHERE ass.code = 'PENDING_PROVIDER_CONFIRMATION'
                      AND ja.confirmation_deadline IS NOT NULL
                      AND ja.confirmation_deadline <= CURRENT_TIMESTAMP
                    FOR UPDATE SKIP LOCKED
                    """
                )
                rows = cursor.fetchall()
                expired = 0
                for row in rows:
                    cursor.execute(
                        "SELECT id FROM assignment_statuses WHERE code = 'CANCELLED' LIMIT 1"
                    )
                    cancelled = cursor.fetchone()
                    cursor.execute(
                        """
                        UPDATE job_assignments
                        SET status_id = %s,
                            cancelled_at = CURRENT_TIMESTAMP,
                            decline_reason = 'Provider confirmation expired'
                        WHERE id = %s
                        """,
                        (cancelled["id"], row["id"]),
                    )
                    cursor.execute(
                        "SELECT id FROM job_statuses WHERE code = 'OPEN' LIMIT 1"
                    )
                    open_status = cursor.fetchone()
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
                        (open_status["id"], row["job_id"]),
                    )
                    expired += 1
                connection.commit()
                return expired
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()


    def expire_completion_confirmations(self):
        # Do not auto-mark disputed work as paid. Expired confirmation becomes
        # a reviewable state; financial settlement is intentionally separate.
        from app.database import db_connection
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT ja.id
                    FROM job_assignments ja
                    INNER JOIN job_execution_statuses jes
                        ON jes.id = ja.execution_status_id
                    WHERE jes.code = 'COMPLETED_PENDING_CONFIRMATION'
                      AND ja.customer_confirmation_deadline IS NOT NULL
                      AND ja.customer_confirmation_deadline <= CURRENT_TIMESTAMP
                    FOR UPDATE SKIP LOCKED
                    """
                )
                rows = cursor.fetchall()
                status = cursor.execute(
                    "SELECT id FROM job_execution_statuses WHERE code = 'DISPUTED' LIMIT 1"
                )
                cursor.execute(
                    "SELECT id FROM job_execution_statuses WHERE code = 'DISPUTED' LIMIT 1"
                )
                disputed = cursor.fetchone()
                for row in rows:
                    cursor.execute(
                        """
                        UPDATE job_assignments
                        SET execution_status_id = %s
                        WHERE id = %s
                        """,
                        (disputed["id"], row["id"]),
                    )
                connection.commit()
                return len(rows)
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def run_once(self):
        job = self.claim()
        if not job:
            return False

        try:
            payload = json.loads(job["payload_json"])
            if job["job_type"] == "MATCH_JOB":
                self.matching.dispatch_job(int(payload["job_id"]))
            elif job["job_type"] == "EXPIRE_ASSIGNMENTS":
                self.expire_assignments()
            elif job["job_type"] == "EXPIRE_COMPLETION_CONFIRMATIONS":
                self.expire_completion_confirmations()
            else:
                raise RuntimeError(f"Unknown worker job type: {job['job_type']}")
            self.finish(job["id"], True)
        except Exception as exc:
            self.finish(job["id"], False, exc)
        return True


def main():
    parser = argparse.ArgumentParser(description="Marketplace background worker")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--sleep", type=float, default=2.0)
    args = parser.parse_args()

    worker = Worker()
    if args.once:
        worker.run_once()
        return

    while True:
        did_work = worker.run_once()
        if not did_work:
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
