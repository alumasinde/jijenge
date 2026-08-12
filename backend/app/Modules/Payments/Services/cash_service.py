import uuid

from fastapi import HTTPException

from app.database import db_connection


class CashService:
    def confirm(self, cash_record_id: int, recorder_user_id: int,
                receipt_reference: str | None, notes: str | None):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT
                        cpr.id,cpr.payment_intent_id,cpr.amount,
                        cs.code AS cash_status,
                        pi.payer_user_id,pi.currency_code
                    FROM cash_payment_records cpr
                    INNER JOIN cash_payment_statuses cs ON cs.id=cpr.status_id
                    INNER JOIN payment_intents pi ON pi.id=cpr.payment_intent_id
                    WHERE cpr.id=%s
                    FOR UPDATE
                    """,
                    (cash_record_id,),
                )
                record=cursor.fetchone()
                if not record:
                    raise HTTPException(status_code=404,detail="Cash payment not found")
                if record["cash_status"] == "CONFIRMED":
                    cursor.execute(
                        """
                        SELECT id
                        FROM payment_transactions
                        WHERE payment_intent_id=%s
                          AND idempotency_key=%s
                        LIMIT 1
                        """,
                        (record["payment_intent_id"],f"cash-confirm:{cash_record_id}"),
                    )
                    tx=cursor.fetchone()
                    connection.commit(); cursor.close()
                    return {
                        "success":True,
                        "already_confirmed":True,
                        "transaction_id":int(tx["id"]) if tx else None,
                    }

                cursor.execute(
                    "SELECT id FROM cash_payment_statuses WHERE code='CONFIRMED' LIMIT 1"
                )
                confirmed_id=cursor.fetchone()["id"]

                cursor.execute(
                    """
                    UPDATE cash_payment_records
                    SET status_id=%s,recorded_by_user_id=%s,
                        receipt_reference=%s,confirmation_notes=%s,
                        confirmed_at=CURRENT_TIMESTAMP,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,
                    (
                        confirmed_id,recorder_user_id,receipt_reference,
                        notes,cash_record_id,
                    ),
                )

                cursor.execute(
                    "SELECT id FROM payment_statuses WHERE code='SUCCEEDED' LIMIT 1"
                )
                success_id=cursor.fetchone()["id"]

                cursor.execute(
                    """
                    INSERT INTO payment_transactions
                    (
                        public_id,payment_intent_id,payment_status_id,
                        transaction_type,amount,currency_code,provider_code,
                        provider_reference,idempotency_key,processed_at
                    )
                    VALUES
                    (%s,%s,%s,'CHARGE',%s,%s,'CASH',%s,%s,CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)
                    """,
                    (
                        str(uuid.uuid4()),record["payment_intent_id"],
                        success_id,record["amount"],record["currency_code"],
                        receipt_reference,f"cash-confirm:{cash_record_id}",
                    ),
                )
                transaction_id=int(cursor.lastrowid)

                cursor.execute(
                    """
                    UPDATE payment_intents
                    SET payment_status_id=%s,provider_code='CASH',
                        provider_reference=%s,succeeded_at=CURRENT_TIMESTAMP,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,
                    (success_id,receipt_reference,record["payment_intent_id"]),
                )
                connection.commit()
            except HTTPException:
                connection.rollback(); cursor.close(); raise
            except Exception:
                connection.rollback(); cursor.close(); raise
            cursor.close()

        from app.Modules.Financials.Services.payment_success_service import PaymentSuccessService
        financial=PaymentSuccessService().finalize(
            payment_intent_id=int(record["payment_intent_id"]),
            payment_transaction_id=transaction_id,
        )
        return {
            "success":True,
            "transaction_id":transaction_id,
            "payment_intent_id":int(record["payment_intent_id"]),
            "financial":financial,
        }
