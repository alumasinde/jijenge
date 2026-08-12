import uuid
from decimal import Decimal

from app.database import db_connection


class LedgerService:
    def _type(self,cursor,code):
        cursor.execute(
            "SELECT id FROM ledger_entry_types WHERE code=%s LIMIT 1",(code,)
        )
        row=cursor.fetchone()
        if not row: raise RuntimeError(f"Ledger entry type {code} missing")
        return int(row["id"])

    def post(
        self, entry_type, amount, direction, currency_code="KES",
        payment_transaction_id=None, refund_id=None, settlement_id=None,
        provider_earning_id=None, job_id=None, assignment_id=None,
        reference=None, description=None
    ):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    INSERT INTO financial_ledger_entries
                    (
                        public_id,entry_type_id,payment_transaction_id,
                        refund_id,settlement_id,provider_earning_id,
                        job_id,assignment_id,amount,currency_code,
                        direction,reference,description
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        str(uuid.uuid4()),self._type(cursor,entry_type),
                        payment_transaction_id,refund_id,settlement_id,
                        provider_earning_id,job_id,assignment_id,
                        Decimal(str(amount)),currency_code,direction,
                        reference,description,
                    ),
                )
                entry_id=int(cursor.lastrowid)
                connection.commit()
            except Exception:
                connection.rollback();raise
            finally:
                cursor.close()
        return entry_id

    def post_payment_breakdown(self,payment_transaction_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT
                        pt.id,pt.amount,pt.currency_code,
                        pi.job_id,ja.id AS assignment_id
                    FROM payment_transactions pt
                    INNER JOIN payment_intents pi ON pi.id=pt.payment_intent_id
                    LEFT JOIN job_assignments ja ON ja.job_id=pi.job_id
                    WHERE pt.id=%s
                    LIMIT 1
                    """,(payment_transaction_id,),
                )
                row=cursor.fetchone()
                if not row: return 0

                cursor.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM financial_ledger_entries
                    WHERE payment_transaction_id=%s
                    """,(payment_transaction_id,),
                )
                if int(cursor.fetchone()["count"])>0:
                    return 0

                cursor.execute(
                    """
                    INSERT INTO financial_ledger_entries
                    (
                        public_id,entry_type_id,payment_transaction_id,
                        job_id,assignment_id,amount,currency_code,
                        direction,reference,description
                    )
                    SELECT
                        %s,let.id,%s,%s,%s,%s,%s,'CREDIT',
                        CONCAT('PAYMENT-',%s),'Customer payment received'
                    FROM ledger_entry_types let
                    WHERE let.code='CUSTOMER_PAYMENT'
                    LIMIT 1
                    """,
                    (
                        str(uuid.uuid4()),payment_transaction_id,
                        row["job_id"],row["assignment_id"],row["amount"],
                        row["currency_code"],payment_transaction_id,
                    ),
                )
                connection.commit()
                return int(cursor.rowcount)
            except Exception:
                connection.rollback();raise
            finally:
                cursor.close()
