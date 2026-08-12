from decimal import Decimal
from app.database import db_connection


class ReconciliationService:
    def reconcile_transaction(
        self, transaction_id, provider_amount, provider_currency,
        provider_transaction_id=None, provider_reference=None
    ):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT pt.id,pt.amount,pt.currency_code,
                           pt.provider_code,pt.provider_transaction_id,
                           pt.provider_reference
                    FROM payment_transactions pt
                    WHERE pt.id=%s
                    LIMIT 1
                    """,
                    (transaction_id,),
                )
                tx=cursor.fetchone()
                if not tx:
                    raise ValueError("Payment transaction not found")

                amount_ok=Decimal(str(tx["amount"])) == Decimal(str(provider_amount))
                currency_ok=tx["currency_code"] == provider_currency
                status_code="MATCHED" if amount_ok and currency_ok else "EXCEPTION"
                reason=None if status_code=="MATCHED" else "Amount or currency mismatch"

                cursor.execute(
                    "SELECT id FROM payment_reconciliation_statuses WHERE code=%s LIMIT 1",
                    (status_code,),
                )
                status_id=cursor.fetchone()["id"]
                cursor.execute(
                    """
                    INSERT INTO payment_reconciliation_records
                    (
                        payment_transaction_id,status_id,provider_code,
                        provider_transaction_id,provider_reference,
                        provider_amount,provider_currency,mismatch_reason,
                        checked_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        status_id=VALUES(status_id),
                        provider_transaction_id=VALUES(provider_transaction_id),
                        provider_reference=VALUES(provider_reference),
                        provider_amount=VALUES(provider_amount),
                        provider_currency=VALUES(provider_currency),
                        mismatch_reason=VALUES(mismatch_reason),
                        checked_at=CURRENT_TIMESTAMP
                    """,
                    (
                        transaction_id,status_id,tx["provider_code"],
                        provider_transaction_id,provider_reference,
                        provider_amount,provider_currency,reason,
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback(); cursor.close(); raise
            cursor.close()
        return {"transaction_id":transaction_id,"status":status_code,"reason":reason}
