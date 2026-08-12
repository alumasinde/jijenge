import uuid
from decimal import Decimal

from fastapi import HTTPException

from app.database import db_connection


class JobPaymentService:
    """
    Creates the customer-side payment record for a completed job.

    The provider is not paid merely because a payment intent exists.
    Successful customer payment is required first. Commission and provider
    earnings are finalized separately after customer confirmation.
    """

    def _status(self, cursor, code):
        cursor.execute(
            "SELECT id FROM job_payment_statuses WHERE code=%s LIMIT 1",
            (code,),
        )
        row=cursor.fetchone()
        if not row:
            raise RuntimeError(f"Job payment status {code} is missing")
        return int(row["id"])

    def _method(self, cursor, code):
        cursor.execute(
            """
            SELECT id, code, provider_code, requires_manual_confirmation
            FROM payment_methods
            WHERE code=%s AND is_active=1
            LIMIT 1
            """,
            (code.upper(),),
        )
        row=cursor.fetchone()
        if not row:
            raise HTTPException(status_code=422, detail="Payment method is unavailable")
        return row

    def _get(self, cursor, payment_id, customer_id):
        cursor.execute(
            """
            SELECT
                jpr.id,jpr.public_id,jpr.assignment_id,jpr.job_id,
                jpr.amount,jpr.currency_code,
                pm.code AS payment_method,
                jps.code AS status,
                jpr.payment_intent_id,jpr.payment_reference,
                jpr.paid_at,jpr.failure_reason
            FROM job_payment_records jpr
            INNER JOIN payment_methods pm ON pm.id=jpr.payment_method_id
            INNER JOIN job_payment_statuses jps ON jps.id=jpr.status_id
            WHERE jpr.id=%s AND jpr.payer_user_id=%s
            LIMIT 1
            """,
            (payment_id,customer_id),
        )
        return cursor.fetchone()

    def create(self, assignment_id, customer_id, payment_method, idempotency_key):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT
                        ja.id,ja.job_id,ja.provider_id,
                        ja.assigned_by_user_id,
                        jes.code AS execution_status,
                        j.customer_id,j.agreed_amount
                    FROM job_assignments ja
                    INNER JOIN jobs j ON j.id=ja.job_id
                    INNER JOIN job_execution_statuses jes
                        ON jes.id=ja.execution_status_id
                    WHERE ja.id=%s
                    FOR UPDATE
                    """,
                    (assignment_id,),
                )
                assignment=cursor.fetchone()
                if not assignment or int(assignment["customer_id"]) != customer_id:
                    raise HTTPException(status_code=404,detail="Assignment not found")
                if assignment["execution_status"] != "COMPLETED":
                    raise HTTPException(
                        status_code=409,
                        detail="Payment can only be created after customer confirms completion",
                    )

                cursor.execute(
                    """
                    SELECT *
                    FROM job_payment_records
                    WHERE payer_user_id=%s AND idempotency_key=%s
                    LIMIT 1
                    """,
                    (customer_id,idempotency_key),
                )
                existing=cursor.fetchone()
                if existing:
                    row=self._get(cursor,existing["id"],customer_id)
                    connection.commit()
                    cursor.close()
                    return row

                method=self._method(cursor,payment_method)
                pending=self._status(cursor,"PENDING")
                amount=Decimal(str(assignment["agreed_amount"]))
                if amount <= 0:
                    raise HTTPException(status_code=409,detail="Job amount must be greater than zero")

                cursor.execute(
                    """
                    INSERT INTO job_payment_records
                    (
                        public_id,assignment_id,job_id,payer_user_id,
                        amount,currency_code,payment_method_id,status_id,
                        idempotency_key
                    )
                    VALUES (%s,%s,%s,%s,%s,'KES',%s,%s,%s)
                    """,
                    (
                        str(uuid.uuid4()),assignment_id,assignment["job_id"],
                        customer_id,amount,method["id"],pending,idempotency_key,
                    ),
                )
                payment_id=int(cursor.lastrowid)

                cursor.execute(
                    """
                    INSERT INTO job_payment_events
                        (job_payment_record_id,event_type_id,actor_user_id,notes)
                    SELECT %s,id,%s,'Job payment created'
                    FROM job_payment_event_types
                    WHERE code='CREATED' LIMIT 1
                    """,
                    (payment_id,customer_id),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return self.get(payment_id,customer_id)

    def create_intent(self,payment_id,customer_id):
        from app.Modules.Payments.Repositories.payment_repository import PaymentRepository
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                row=self._get(cursor,payment_id,customer_id)
                if not row:
                    raise HTTPException(status_code=404,detail="Job payment not found")
                if row["status"] == "PAID":
                    connection.commit()
                    cursor.close()
                    return row

                intent=PaymentRepository().get_or_create_intent(
                    payer_user_id=customer_id,
                    job_id=row["job_id"],
                    payment_method=row["payment_method"],
                    amount=row["amount"],
                    currency_code=row["currency_code"],
                    description=f"Payment for completed job #{row['job_id']}",
                    idempotency_key=f"job-payment:{payment_id}",
                )
                cursor.execute(
                    """
                    UPDATE job_payment_records
                    SET payment_intent_id=%s,
                        status_id=(SELECT id FROM job_payment_statuses WHERE code='PROCESSING' LIMIT 1),
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s AND payer_user_id=%s
                    """,
                    (intent["id"],payment_id,customer_id),
                )
                cursor.execute(
                    """
                    INSERT INTO job_payment_events
                        (job_payment_record_id,event_type_id,actor_user_id,notes)
                    SELECT %s,id,%s,'Payment intent created'
                    FROM job_payment_event_types
                    WHERE code='PAYMENT_INTENT_CREATED' LIMIT 1
                    """,
                    (payment_id,customer_id),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
        return self.get(payment_id,customer_id)

    def get(self,payment_id,customer_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            row=self._get(cursor,payment_id,customer_id)
            cursor.close()
        if not row:
            raise HTTPException(status_code=404,detail="Job payment not found")
        return row
