import hashlib
import json
import uuid
from decimal import Decimal

from app.database import db_connection


class ProviderRequestService:
    def _status(self,cursor,code):
        cursor.execute(
            "SELECT id FROM payment_provider_request_statuses WHERE code=%s LIMIT 1",
            (code,),
        )
        row=cursor.fetchone()
        if not row: raise RuntimeError(f"Provider request status {code} missing")
        return int(row["id"])

    def create_or_get(
        self, provider_code, operation_code, idempotency_key,
        payment_intent_id=None, payment_transaction_id=None,
        refund_id=None, settlement_id=None, request_payload=None
    ):
        payload=request_payload or {}
        request_hash=hashlib.sha256(
            json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
        ).hexdigest()

        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT *
                    FROM payment_provider_requests
                    WHERE provider_code=%s
                      AND operation_code=%s
                      AND idempotency_key=%s
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (provider_code,operation_code,idempotency_key),
                )
                existing=cursor.fetchone()
                if existing:
                    connection.commit(); cursor.close()
                    return existing

                cursor.execute(
                    """
                    INSERT INTO payment_provider_requests
                    (
                        public_id,provider_code,operation_code,
                        payment_intent_id,payment_transaction_id,
                        refund_id,settlement_id,idempotency_key,
                        status_id,request_hash
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        str(uuid.uuid4()),provider_code,operation_code,
                        payment_intent_id,payment_transaction_id,
                        refund_id,settlement_id,idempotency_key,
                        self._status(cursor,"CREATED"),request_hash,
                    ),
                )
                request_id=int(cursor.lastrowid)
                connection.commit()
            except Exception:
                connection.rollback(); cursor.close(); raise
            cursor.close()
        return self.get(request_id)

    def update_result(self,request_id,status_code,provider_request_id=None,
                      provider_reference=None,response=None,failure_reason=None):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                UPDATE payment_provider_requests
                SET status_id=(
                    SELECT id FROM payment_provider_request_statuses
                    WHERE code=%s LIMIT 1
                ),
                provider_request_id=%s,
                provider_reference=%s,
                response_json=%s,
                failure_reason=%s,
                updated_at=CURRENT_TIMESTAMP
                WHERE id=%s
                """,
                (
                    status_code,provider_request_id,provider_reference,
                    json.dumps(response or {}),failure_reason,request_id,
                ),
            )
            connection.commit()
            cursor.close()
        return self.get(request_id)

    def get(self,request_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT ppr.*,pprs.code AS status
                FROM payment_provider_requests ppr
                INNER JOIN payment_provider_request_statuses pprs
                    ON pprs.id=ppr.status_id
                WHERE ppr.id=%s
                LIMIT 1
                """,(request_id,),
            )
            row=cursor.fetchone(); cursor.close()
        return row
