import uuid
from decimal import Decimal
from fastapi import HTTPException

from app.database import db_connection


class RefundService:
    def _status(self,cursor,code):
        cursor.execute("SELECT id FROM refund_statuses WHERE code=%s LIMIT 1",(code,))
        row=cursor.fetchone()
        if not row: raise RuntimeError(f"Refund status {code} missing")
        return int(row["id"])

    def request(self,user_id,payment_id,amount,reason,idempotency_key,dispute_id=None):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT jpr.id,jpr.amount,jpr.payer_user_id,
                           jpr.currency_code,jps.code AS payment_status
                    FROM job_payment_records jpr
                    INNER JOIN job_payment_statuses jps ON jps.id=jpr.status_id
                    WHERE jpr.id=%s
                    FOR UPDATE
                    """,(payment_id,),
                )
                payment=cursor.fetchone()
                if not payment: raise HTTPException(status_code=404,detail="Payment not found")
                if int(payment["payer_user_id"])!=user_id:
                    raise HTTPException(status_code=403,detail="You cannot refund this payment")
                if payment["payment_status"]!="PAID":
                    raise HTTPException(status_code=409,detail="Only paid payments can be refunded")

                requested=Decimal(str(amount))
                paid=Decimal(str(payment["amount"]))
                if requested<=0 or requested>paid:
                    raise HTTPException(status_code=422,detail="Invalid refund amount")

                cursor.execute(
                    """
                    SELECT COALESCE(SUM(r.approved_amount),0) AS refunded
                    FROM refunds r
                    INNER JOIN refund_statuses rs ON rs.id=r.status_id
                    WHERE r.job_payment_record_id=%s
                      AND rs.code IN ('APPROVED','PROCESSING','PAID')
                    """,(payment_id,),
                )
                already=Decimal(str(cursor.fetchone()["refunded"]))
                if already+requested>paid:
                    raise HTTPException(status_code=409,detail="Refund exceeds remaining refundable amount")

                cursor.execute(
                    """
                    SELECT id FROM refunds
                    WHERE requested_by_user_id=%s AND idempotency_key=%s
                    LIMIT 1
                    """,(user_id,idempotency_key),
                )
                existing=cursor.fetchone()
                if existing:
                    connection.commit();cursor.close()
                    return self.get(user_id,existing["id"])

                cursor.execute(
                    """
                    INSERT INTO refunds
                    (
                        public_id,job_payment_record_id,dispute_id,
                        requested_by_user_id,status_id,requested_amount,
                        currency_code,reason,idempotency_key
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        str(uuid.uuid4()),payment_id,dispute_id,user_id,
                        self._status(cursor,"REQUESTED"),requested,
                        payment["currency_code"],reason,idempotency_key,
                    ),
                )
                refund_id=int(cursor.lastrowid)
                cursor.execute(
                    """
                    INSERT INTO refund_events
                        (refund_id,event_type_id,actor_user_id,notes)
                    SELECT %s,id,%s,'Refund requested'
                    FROM refund_event_types WHERE code='REQUESTED' LIMIT 1
                    """,(refund_id,user_id),
                )
                connection.commit()
            except Exception:
                connection.rollback();cursor.close();raise
            cursor.close()
        return self.get(user_id,refund_id)

    def approve(self,admin_id,refund_id,approved_amount,notes=None):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT r.*,rs.code AS status
                    FROM refunds r
                    INNER JOIN refund_statuses rs ON rs.id=r.status_id
                    WHERE r.id=%s FOR UPDATE
                    """,(refund_id,),
                )
                refund=cursor.fetchone()
                if not refund: raise HTTPException(status_code=404,detail="Refund not found")
                if refund["status"]!="REQUESTED":
                    raise HTTPException(status_code=409,detail="Refund is not awaiting approval")

                amount=Decimal(str(approved_amount))
                requested=Decimal(str(refund["requested_amount"]))
                if amount<=0 or amount>requested:
                    raise HTTPException(status_code=422,detail="Invalid approved refund amount")

                cursor.execute(
                    """
                    UPDATE refunds
                    SET status_id=%s,approved_amount=%s,
                        approved_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,(self._status(cursor,"APPROVED"),amount,refund_id),
                )
                cursor.execute(
                    """
                    INSERT INTO refund_events
                        (refund_id,event_type_id,actor_user_id,notes)
                    SELECT %s,id,%s,%s
                    FROM refund_event_types WHERE code='APPROVED' LIMIT 1
                    """,(refund_id,admin_id,notes),
                )
                connection.commit()
            except Exception:
                connection.rollback();cursor.close();raise
            cursor.close()
        return {"refund_id":refund_id,"status":"APPROVED","approved_amount":amount}

    def get(self,user_id,refund_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT r.id,r.public_id,r.job_payment_record_id,
                       r.requested_amount,r.approved_amount,r.paid_amount,
                       r.currency_code,rs.code AS status,r.reason,
                       r.provider_reference,r.requested_at,r.approved_at,r.paid_at,
                       r.failure_reason
                FROM refunds r
                INNER JOIN refund_statuses rs ON rs.id=r.status_id
                WHERE r.id=%s AND r.requested_by_user_id=%s
                LIMIT 1
                """,(refund_id,user_id),
            )
            row=cursor.fetchone();cursor.close()
        if not row: raise HTTPException(status_code=404,detail="Refund not found")
        return row
