from decimal import Decimal

from fastapi import HTTPException

from app.database import db_connection
from app.Modules.Financials.Services.commission_service import CommissionService


class PaymentSuccessService:
    """
    Canonical success path for a customer payment.

    1. Verify the payment intent belongs to a real job payment or is otherwise
       a legitimate job transaction.
    2. Validate amount/currency against the job payment.
    3. Mark the job payment PAID.
    4. Finalize platform commission/provider earning once.
    """

    def finalize(self, payment_intent_id: int, payment_transaction_id: int):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT
                        jpr.id AS job_payment_id,
                        jpr.assignment_id,
                        jpr.amount AS expected_amount,
                        jpr.currency_code AS expected_currency,
                        jpr.status_id AS job_payment_status_id,
                        pt.amount AS transaction_amount,
                        pt.currency_code AS transaction_currency,
                        ps.code AS transaction_status
                    FROM job_payment_records jpr
                    INNER JOIN payment_transactions pt
                        ON pt.payment_intent_id=jpr.payment_intent_id
                    INNER JOIN payment_statuses ps
                        ON ps.id=pt.payment_status_id
                    WHERE jpr.payment_intent_id=%s
                      AND pt.id=%s
                    FOR UPDATE
                    """,
                    (payment_intent_id,payment_transaction_id),
                )
                row=cursor.fetchone()
                if not row:
                    raise HTTPException(
                        status_code=409,
                        detail="Successful payment is not linked to a valid job payment",
                    )
                if row["transaction_status"] != "SUCCEEDED":
                    raise HTTPException(status_code=409,detail="Payment transaction is not successful")

                if Decimal(str(row["expected_amount"])) != Decimal(str(row["transaction_amount"])):
                    raise HTTPException(status_code=409,detail="Payment amount mismatch")
                if row["expected_currency"] != row["transaction_currency"]:
                    raise HTTPException(status_code=409,detail="Payment currency mismatch")

                cursor.execute(
                    "SELECT id FROM job_payment_statuses WHERE code='PAID' LIMIT 1"
                )
                paid_id=cursor.fetchone()["id"]

                cursor.execute(
                    """
                    UPDATE job_payment_records
                    SET status_id=%s,
                        payment_reference=(
                            SELECT provider_reference
                            FROM payment_transactions
                            WHERE id=%s
                        ),
                        paid_at=COALESCE(paid_at,CURRENT_TIMESTAMP),
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,
                    (paid_id,payment_transaction_id,row["job_payment_id"]),
                )

                cursor.execute(
                    """
                    INSERT INTO job_payment_events
                        (job_payment_record_id,event_type_id,notes)
                    SELECT %s,id,'Customer payment successfully confirmed'
                    FROM job_payment_event_types
                    WHERE code='PAYMENT_SUCCEEDED' LIMIT 1
                    """,
                    (row["job_payment_id"],),
                )
                connection.commit()
            except Exception:
                connection.rollback(); cursor.close(); raise
            cursor.close()

        # Commission service is idempotent via unique assignment breakdown.
        breakdown_id=CommissionService().finalize_job_financials(
            int(row["assignment_id"]), Decimal("0.00")
        )
        return {
            "payment_intent_id": payment_intent_id,
            "payment_transaction_id": payment_transaction_id,
            "job_payment_id": int(row["job_payment_id"]),
            "financial_breakdown_id": breakdown_id,
        }
