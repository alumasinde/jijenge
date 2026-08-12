import json
import uuid
from decimal import Decimal
from fastapi import HTTPException

from app.database import db_connection
from app.config import settings
from app.Modules.Payments.Providers.registry import PaymentProviderRegistry


class FinancialExecutionService:
    def __init__(self):
        self.providers = PaymentProviderRegistry(settings)

    def _status(self, cursor, code):
        cursor.execute(
            "SELECT id FROM financial_execution_statuses WHERE code=%s LIMIT 1",
            (code,),
        )
        row=cursor.fetchone()
        if not row:
            raise RuntimeError(f"Financial execution status {code} missing")
        return int(row["id"])

    def queue_settlement(self, settlement_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT
                        ps.id,ps.provider_id,ps.amount,ps.currency_code,
                        ppm.account_reference,ppmt.code AS provider_code,
                        pss.code AS settlement_status
                    FROM provider_settlements ps
                    INNER JOIN provider_settlement_statuses pss
                        ON pss.id=ps.status_id
                    INNER JOIN provider_payout_methods ppm
                        ON ppm.id=ps.provider_payout_method_id
                    INNER JOIN provider_payout_method_types ppmt
                        ON ppmt.id=ppm.method_type_id
                    WHERE ps.id=%s
                    FOR UPDATE
                    """,(settlement_id,),
                )
                settlement=cursor.fetchone()
                if not settlement:
                    raise HTTPException(status_code=404,detail="Settlement not found")
                if settlement["settlement_status"]!="REQUESTED":
                    raise HTTPException(status_code=409,detail="Settlement is not requestable")

                cursor.execute(
                    """
                    SELECT id
                    FROM financial_executions
                    WHERE settlement_id=%s
                      AND status_id NOT IN (
                        SELECT id FROM financial_execution_statuses
                        WHERE code='FAILED'
                      )
                    LIMIT 1
                    """,(settlement_id,),
                )
                existing=cursor.fetchone()
                if existing:
                    connection.commit();cursor.close()
                    return int(existing["id"])

                cursor.execute(
                    """
                    INSERT INTO financial_executions
                    (
                        public_id,execution_type,provider_code,status_id,
                        settlement_id,next_attempt_at
                    )
                    VALUES (%s,'PAYOUT',%s,%s,%s,CURRENT_TIMESTAMP)
                    """,
                    (
                        str(uuid.uuid4()),settlement["provider_code"],
                        self._status(cursor,"QUEUED"),settlement_id,
                    ),
                )
                execution_id=int(cursor.lastrowid)
                connection.commit()
            except Exception:
                connection.rollback();cursor.close();raise
            cursor.close()
        return execution_id

    def execute_settlement(self, execution_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT
                        fe.*,ps.amount,ps.currency_code,
                        ppm.account_reference,
                        ps.id AS settlement_id
                    FROM financial_executions fe
                    INNER JOIN provider_settlements ps
                        ON ps.id=fe.settlement_id
                    INNER JOIN provider_payout_methods ppm
                        ON ppm.id=ps.provider_payout_method_id
                    INNER JOIN financial_execution_statuses fes
                        ON fes.id=fe.status_id
                    WHERE fe.id=%s
                    FOR UPDATE
                    """,(execution_id,),
                )
                execution=cursor.fetchone()
                if not execution:
                    raise HTTPException(status_code=404,detail="Execution not found")
                if execution["status"] in ("SUCCEEDED","PROCESSING"):
                    connection.commit();cursor.close()
                    return execution
                cursor.execute(
                    """
                    UPDATE financial_executions
                    SET status_id=%s,attempt_count=attempt_count+1,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,(self._status(cursor,"PROCESSING"),execution_id),
                )
                attempt=int(execution["attempt_count"])+1
                connection.commit()
            except Exception:
                connection.rollback();cursor.close();raise
            cursor.close()

        provider=self.providers.get(execution["provider_code"])
        try:
            result=provider.request_payout(
                amount=Decimal(str(execution["amount"])),
                currency_code=execution["currency_code"],
                payout_reference=f"SETTLEMENT-{execution['settlement_id']}",
                destination_reference=execution["account_reference"],
                idempotency_key=f"settlement:{execution['settlement_id']}",
            )
        except Exception as exc:
            return self._finish_execution(
                execution_id,attempt,"RETRYABLE",None,None,None,str(exc)
            )

        status="SUCCEEDED" if result.status=="SUCCEEDED" else (
            "RETRYABLE" if result.status in ("SENT","PENDING") else "FAILED"
        )
        return self._finish_execution(
            execution_id,attempt,status,
            result.provider_reference,result.provider_request_id,
            None,result.message,result.response
        )

    def _finish_execution(
        self,execution_id,attempt,status,provider_reference,
        provider_request_id,provider_transaction_id,error,response=None
    ):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT settlement_id,refund_id
                    FROM financial_executions WHERE id=%s FOR UPDATE
                    """,(execution_id,),
                )
                execution=cursor.fetchone()
                status_id=self._status(cursor,status)
                cursor.execute(
                    """
                    UPDATE financial_executions
                    SET status_id=%s,provider_reference=%s,
                        provider_transaction_id=%s,last_error=%s,
                        last_response_json=%s,
                        completed_at=CASE
                            WHEN %s='SUCCEEDED' THEN CURRENT_TIMESTAMP
                            ELSE completed_at
                        END,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,
                    (
                        status_id,provider_reference,provider_transaction_id,
                        error,json.dumps(response or {}),
                        status,execution_id,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO financial_execution_events
                    (
                        execution_id,status_id,attempt_number,
                        provider_reference,provider_transaction_id,
                        response_json,error_message
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        execution_id,status_id,attempt,provider_reference,
                        provider_transaction_id,json.dumps(response or {}),
                        error,
                    ),
                )
                if status=="SUCCEEDED" and execution["settlement_id"]:
                    cursor.execute(
                        """
                        UPDATE provider_settlements
                        SET status_id=(
                            SELECT id FROM provider_settlement_statuses
                            WHERE code='PROCESSING' LIMIT 1
                        ),
                        payout_reference=COALESCE(%s,payout_reference),
                        processing_at=CURRENT_TIMESTAMP
                        WHERE id=%s
                        """,
                        (provider_reference,execution["settlement_id"]),
                    )
                connection.commit()
            except Exception:
                connection.rollback();cursor.close();raise
            cursor.close()
        return {"execution_id":execution_id,"status":status}

    def queue_refund(self, refund_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT
                        r.id,r.approved_amount,r.currency_code,
                        r.provider_reference,rs.code AS refund_status,
                        jpr.provider_transaction_id,
                        jpr.provider_code
                    FROM refunds r
                    INNER JOIN refund_statuses rs ON rs.id=r.status_id
                    INNER JOIN job_payment_records jpr
                        ON jpr.id=r.job_payment_record_id
                    WHERE r.id=%s FOR UPDATE
                    """,(refund_id,),
                )
                refund=cursor.fetchone()
                if not refund:
                    raise HTTPException(status_code=404,detail="Refund not found")
                if refund["refund_status"]!="APPROVED":
                    raise HTTPException(status_code=409,detail="Refund is not approved")

                cursor.execute(
                    """
                    INSERT INTO financial_executions
                    (
                        public_id,execution_type,provider_code,status_id,
                        refund_id,next_attempt_at
                    )
                    SELECT
                        %s,'REFUND',%s,%s,%s,CURRENT_TIMESTAMP
                    WHERE NOT EXISTS (
                        SELECT 1 FROM financial_executions
                        WHERE refund_id=%s AND execution_type='REFUND'
                          AND status_id NOT IN (
                            SELECT id FROM financial_execution_statuses
                            WHERE code='FAILED'
                          )
                    )
                    """,
                    (
                        str(uuid.uuid4()),refund["provider_code"],
                        self._status(cursor,"QUEUED"),refund_id,refund_id,
                    ),
                )
                execution_id=int(cursor.lastrowid)
                connection.commit()
            except Exception:
                connection.rollback();cursor.close();raise
            cursor.close()
        return execution_id

    def execute_refund(self,execution_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT fe.id,fe.attempt_count,
                       r.approved_amount,r.currency_code,
                       jpr.provider_transaction_id,
                       r.provider_code
                FROM financial_executions fe
                INNER JOIN refunds r ON r.id=fe.refund_id
                INNER JOIN job_payment_records jpr
                    ON jpr.id=r.job_payment_record_id
                WHERE fe.id=%s
                FOR UPDATE
                """,(execution_id,),
            )
            row=cursor.fetchone()
            cursor.close()
        if not row: raise HTTPException(status_code=404,detail="Execution not found")
        provider=self.providers.get(row["provider_code"])
        try:
            result=provider.request_refund(
                amount=Decimal(str(row["approved_amount"])),
                currency_code=row["currency_code"],
                provider_transaction_id=row["provider_transaction_id"],
                idempotency_key=f"refund:{execution_id}",
            )
        except Exception as exc:
            return self._finish_execution(
                execution_id,int(row["attempt_count"])+1,
                "RETRYABLE",None,None,None,str(exc)
            )
        status="SUCCEEDED" if result.status=="SUCCEEDED" else (
            "RETRYABLE" if result.status in ("SENT","PENDING") else "FAILED"
        )
        return self._finish_execution(
            execution_id,int(row["attempt_count"])+1,status,
            result.provider_reference,result.provider_request_id,None,
            result.message,result.response
        )
