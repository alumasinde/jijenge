from app.database import db_connection
from app.Modules.Financials.Services.reconciliation_service import ReconciliationService


class ReconciliationWorker:
    """
    Small database-backed worker.

    Run from cron/systemd/Celery/RQ later; it intentionally has no infinite
    loop so deployment controls scheduling.
    """

    def run(self, provider_code="MPESA", limit=100):
        job_id=self._start_job(provider_code)
        scanned=matched=exceptions=0
        try:
            with db_connection() as connection:
                cursor=connection.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT pt.id,pt.amount,pt.currency_code,
                           pt.provider_code,pt.provider_reference,
                           pt.provider_transaction_id
                    FROM payment_transactions pt
                    LEFT JOIN payment_reconciliation_records prr
                        ON prr.payment_transaction_id=pt.id
                    WHERE pt.provider_code=%s
                      AND prr.id IS NULL
                    ORDER BY pt.id
                    LIMIT %s
                    """,(provider_code,limit),
                )
                rows=cursor.fetchall()
                cursor.close()

            service=ReconciliationService()
            for row in rows:
                scanned+=1
                # A local transaction can be structurally matched only when
                # provider confirmation data is available. Otherwise it remains
                # an exception requiring provider-side reconciliation.
                if row["provider_reference"] and row["provider_transaction_id"]:
                    service.reconcile_transaction(
                        row["id"],row["amount"],row["currency_code"],
                        row["provider_transaction_id"],
                        row["provider_reference"],
                    )
                    matched+=1
                else:
                    self._mark_exception(
                        row["id"],provider_code,
                        "Provider confirmation data is incomplete"
                    )
                    exceptions+=1
            self._finish_job(job_id,scanned,matched,exceptions,"COMPLETED",None)
            return {
                "job_id":job_id,"scanned":scanned,
                "matched":matched,"exceptions":exceptions
            }
        except Exception as exc:
            self._finish_job(job_id,scanned,matched,exceptions,"FAILED",str(exc))
            raise

    def _start_job(self,provider_code):
        import uuid
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                INSERT INTO reconciliation_jobs
                    (public_id,provider_code,status_id,started_at)
                VALUES
                    (%s,%s,
                     (SELECT id FROM reconciliation_job_statuses
                      WHERE code='RUNNING' LIMIT 1),
                     CURRENT_TIMESTAMP)
                """,(str(uuid.uuid4()),provider_code),
            )
            job_id=int(cursor.lastrowid)
            connection.commit();cursor.close()
        return job_id

    def _finish_job(self,job_id,scanned,matched,exceptions,status,reason):
        with db_connection() as connection:
            cursor=connection.cursor()
            cursor.execute(
                """
                UPDATE reconciliation_jobs
                SET status_id=(
                    SELECT id FROM reconciliation_job_statuses
                    WHERE code=%s LIMIT 1
                ),
                scanned_count=%s,matched_count=%s,exception_count=%s,
                completed_at=CURRENT_TIMESTAMP,failure_reason=%s
                WHERE id=%s
                """,(status,scanned,matched,exceptions,reason,job_id),
            )
            connection.commit();cursor.close()

    def _mark_exception(self,transaction_id,provider_code,reason):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT id FROM payment_reconciliation_statuses WHERE code='EXCEPTION' LIMIT 1"
            )
            status=cursor.fetchone()["id"]
            cursor.execute(
                """
                INSERT INTO payment_reconciliation_records
                (
                    payment_transaction_id,status_id,provider_code,
                    mismatch_reason,checked_at
                )
                VALUES (%s,%s,%s,%s,CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE
                    status_id=VALUES(status_id),
                    mismatch_reason=VALUES(mismatch_reason),
                    checked_at=CURRENT_TIMESTAMP
                """,
                (transaction_id,status,provider_code,reason),
            )
            connection.commit();cursor.close()
