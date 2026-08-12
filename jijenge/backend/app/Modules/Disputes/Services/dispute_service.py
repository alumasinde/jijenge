import uuid
from decimal import Decimal
from fastapi import HTTPException

from app.database import db_connection


class DisputeService:
    def _status(self,cursor,code):
        cursor.execute("SELECT id FROM dispute_statuses WHERE code=%s LIMIT 1",(code,))
        row=cursor.fetchone()
        if not row: raise RuntimeError(f"Dispute status {code} missing")
        return int(row["id"])

    def _reason(self,cursor,code):
        cursor.execute(
            "SELECT id FROM dispute_reasons WHERE code=%s AND is_active=1 LIMIT 1",
            (code.upper(),),
        )
        row=cursor.fetchone()
        if not row: raise HTTPException(status_code=422,detail="Invalid dispute reason")
        return int(row["id"])

    def open(self,user_id,assignment_id,reason,description,amount):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT ja.id,ja.job_id,j.customer_id,ja.provider_id,
                           jes.code AS execution_status
                    FROM job_assignments ja
                    INNER JOIN jobs j ON j.id=ja.job_id
                    INNER JOIN job_execution_statuses jes ON jes.id=ja.execution_status_id
                    WHERE ja.id=%s
                    FOR UPDATE
                    """,(assignment_id,),
                )
                row=cursor.fetchone()
                if not row: raise HTTPException(status_code=404,detail="Assignment not found")
                if user_id not in (int(row["customer_id"]),int(row["provider_id"])):
                    raise HTTPException(status_code=403,detail="You cannot dispute this assignment")
                if row["execution_status"] not in ("COMPLETED","COMPLETED_PENDING_CONFIRMATION"):
                    raise HTTPException(status_code=409,detail="Assignment is not eligible for dispute")

                cursor.execute(
                    """
                    SELECT id FROM disputes
                    WHERE assignment_id=%s
                      AND status_id NOT IN (
                          SELECT id FROM dispute_statuses
                          WHERE code IN ('CANCELLED','REJECTED')
                      )
                    LIMIT 1
                    """,(assignment_id,),
                )
                if cursor.fetchone():
                    raise HTTPException(status_code=409,detail="An active dispute already exists")

                cursor.execute(
                    """
                    SELECT amount FROM job_payment_records
                    WHERE assignment_id=%s AND status_id=(
                        SELECT id FROM job_payment_statuses WHERE code='PAID' LIMIT 1
                    )
                    LIMIT 1
                    """,(assignment_id,),
                )
                paid=cursor.fetchone()
                disputed=Decimal(str(amount or (paid["amount"] if paid else 0)))
                if disputed < 0 or (paid and disputed > Decimal(str(paid["amount"]))):
                    raise HTTPException(status_code=422,detail="Invalid disputed amount")

                cursor.execute(
                    """
                    INSERT INTO disputes
                    (
                        public_id,job_id,assignment_id,opened_by_user_id,
                        reason_id,status_id,description,disputed_amount
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        str(uuid.uuid4()),row["job_id"],assignment_id,user_id,
                        self._reason(cursor,reason),self._status(cursor,"OPEN"),
                        description,disputed,
                    ),
                )
                dispute_id=int(cursor.lastrowid)
                cursor.execute(
                    """
                    INSERT INTO dispute_events
                        (dispute_id,event_type_id,actor_user_id,notes)
                    SELECT %s,id,%s,'Dispute opened'
                    FROM dispute_event_types WHERE code='OPENED' LIMIT 1
                    """,(dispute_id,user_id),
                )

                # Freeze provider earning if it exists.
                cursor.execute(
                    """
                    UPDATE provider_earnings
                    SET status_id=(
                        SELECT id FROM provider_earning_statuses WHERE code='ON_HOLD' LIMIT 1
                    ),
                    updated_at=CURRENT_TIMESTAMP
                    WHERE assignment_id=%s
                      AND status_id IN (
                          SELECT id FROM provider_earning_statuses
                          WHERE code IN ('AVAILABLE','PENDING')
                      )
                    """,(assignment_id,),
                )
                connection.commit()
            except Exception:
                connection.rollback();cursor.close();raise
            cursor.close()
        return self.get(user_id,dispute_id)

    def get(self,user_id,dispute_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT d.id,d.public_id,d.job_id,d.assignment_id,
                       ds.code AS status,dr.code AS reason,
                       d.description,d.disputed_amount,d.resolved_amount,
                       d.currency_code,d.opened_at,d.resolved_at,
                       d.resolution_notes
                FROM disputes d
                INNER JOIN dispute_statuses ds ON ds.id=d.status_id
                INNER JOIN dispute_reasons dr ON dr.id=d.reason_id
                INNER JOIN jobs j ON j.id=d.job_id
                WHERE d.id=%s AND (
                    d.opened_by_user_id=%s
                    OR j.customer_id=%s
                )
                LIMIT 1
                """,(dispute_id,user_id,user_id),
            )
            row=cursor.fetchone();cursor.close()
        if not row: raise HTTPException(status_code=404,detail="Dispute not found")
        return row

    def resolve(self,admin_user_id,dispute_id,status_code,resolved_amount,notes):
        allowed={"RESOLVED_PROVIDER","RESOLVED_CUSTOMER","PARTIALLY_RESOLVED","REJECTED"}
        if status_code not in allowed:
            raise HTTPException(status_code=422,detail="Invalid resolution status")
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT d.*,ds.code AS current_status,
                           j.agreed_amount
                    FROM disputes d
                    INNER JOIN dispute_statuses ds ON ds.id=d.status_id
                    INNER JOIN jobs j ON j.id=d.job_id
                    WHERE d.id=%s
                    FOR UPDATE
                    """,(dispute_id,),
                )
                dispute=cursor.fetchone()
                if not dispute: raise HTTPException(status_code=404,detail="Dispute not found")
                if dispute["current_status"] not in ("OPEN","UNDER_REVIEW"):
                    raise HTTPException(status_code=409,detail="Dispute is already resolved")

                amount=Decimal(str(resolved_amount or 0))
                max_amount=Decimal(str(dispute["disputed_amount"]))
                if amount<0 or amount>max_amount:
                    raise HTTPException(status_code=422,detail="Invalid resolution amount")

                status_id=self._status(cursor,status_code)
                cursor.execute(
                    """
                    UPDATE disputes
                    SET status_id=%s,resolved_amount=%s,
                        resolved_at=CURRENT_TIMESTAMP,
                        resolved_by_user_id=%s,resolution_notes=%s,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,(status_id,amount,admin_user_id,notes,dispute_id),
                )
                cursor.execute(
                    """
                    INSERT INTO dispute_events
                        (dispute_id,event_type_id,actor_user_id,notes)
                    SELECT %s,id,%s,%s
                    FROM dispute_event_types WHERE code='RESOLVED' LIMIT 1
                    """,(dispute_id,admin_user_id,notes),
                )
                connection.commit()
            except Exception:
                connection.rollback();cursor.close();raise
            cursor.close()
        return {"dispute_id":dispute_id,"status":status_code,"resolved_amount":amount}
