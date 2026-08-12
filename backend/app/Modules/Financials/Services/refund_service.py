import uuid
from decimal import Decimal

from fastapi import HTTPException

from app.database import db_connection


class RefundService:
    def _status_id(self, cursor, code):
        cursor.execute(
            """
            SELECT id
            FROM refund_statuses
            WHERE code = %s AND is_active = 1
            LIMIT 1
            """,
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Refund status {code} is missing")
        return int(row["id"])

    def request(
        self,
        *,
        requester_user_id: int,
        payment_intent_id: int,
        amount: Decimal,
        reason: str | None,
        idempotency_key: str,
    ):
        if amount <= 0:
            raise HTTPException(status_code=422, detail="Refund amount must be positive")

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT
                        pi.id,
                        pi.amount,
                        ps.code AS payment_status
                    FROM payment_intents pi
                    INNER JOIN payment_statuses ps ON ps.id = pi.payment_status_id
                    WHERE pi.id = %s
                      AND pi.payer_user_id = %s
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (payment_intent_id, requester_user_id),
                )
                intent = cursor.fetchone()

                if not intent:
                    raise HTTPException(status_code=404, detail="Payment intent not found")
                if intent["payment_status"] != "SUCCEEDED":
                    raise HTTPException(
                        status_code=409,
                        detail="Only successful payments can be refunded",
                    )

                cursor.execute(
                    """
                    SELECT COALESCE(SUM(r.amount), 0) AS refunded
                    FROM refunds r
                    INNER JOIN refund_statuses rs ON rs.id = r.status_id
                    WHERE r.payment_intent_id = %s
                      AND rs.code IN ('REQUESTED', 'PROCESSING', 'SUCCEEDED')
                    """,
                    (payment_intent_id,),
                )
                refunded = Decimal(cursor.fetchone()["refunded"])
                remaining = Decimal(intent["amount"]) - refunded

                if amount > remaining:
                    raise HTTPException(
                        status_code=409,
                        detail="Refund amount exceeds refundable balance",
                    )

                cursor.execute(
                    """
                    SELECT id
                    FROM refunds
                    WHERE requested_by_user_id = %s
                      AND idempotency_key = %s
                    LIMIT 1
                    """,
                    (requester_user_id, idempotency_key),
                )
                existing = cursor.fetchone()
                if existing:
                    connection.commit()
                    cursor.close()
                    return {"id": int(existing["id"]), "duplicate": True}

                status_id = self._status_id(cursor, "REQUESTED")
                public_id = str(uuid.uuid4())

                cursor.execute(
                    """
                    INSERT INTO refunds
                        (
                            public_id,
                            payment_intent_id,
                            requested_by_user_id,
                            status_id,
                            amount,
                            currency_code,
                            reason,
                            idempotency_key
                        )
                    VALUES (%s, %s, %s, %s, %s, 'KES', %s, %s)
                    """,
                    (
                        public_id,
                        payment_intent_id,
                        requester_user_id,
                        status_id,
                        amount,
                        reason,
                        idempotency_key,
                    ),
                )
                refund_id = cursor.lastrowid
                connection.commit()
            except HTTPException:
                connection.rollback()
                cursor.close()
                raise
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return {
            "id": int(refund_id),
            "public_id": public_id,
            "amount": amount,
            "status": "REQUESTED",
        }
