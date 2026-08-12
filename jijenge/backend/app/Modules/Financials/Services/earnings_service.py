import uuid
from decimal import Decimal

from app.database import db_connection


class EarningsService:
    def _status_id(self, cursor, code):
        cursor.execute(
            """
            SELECT id
            FROM provider_earning_statuses
            WHERE code = %s AND is_active = 1
            LIMIT 1
            """,
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Earning status {code} is missing")
        return int(row["id"] if isinstance(row, dict) else row[0])

    def create_for_job(
        self,
        *,
        provider_user_id: int,
        job_id: int,
        gross_amount: Decimal,
        platform_fee_amount: Decimal,
        adjustment_amount: Decimal = Decimal("0.00"),
    ):
        net_amount = gross_amount - platform_fee_amount + adjustment_amount
        if net_amount < 0:
            raise ValueError("Provider net earnings cannot be negative")

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id, public_id
                    FROM provider_earnings
                    WHERE job_id = %s
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (job_id,),
                )
                existing = cursor.fetchone()
                if existing:
                    connection.commit()
                    cursor.close()
                    return existing

                status_id = self._status_id(cursor, "PENDING")
                public_id = str(uuid.uuid4())

                cursor.execute(
                    """
                    INSERT INTO provider_earnings
                        (
                            public_id,
                            provider_user_id,
                            job_id,
                            status_id,
                            gross_amount,
                            platform_fee_amount,
                            adjustment_amount,
                            net_amount,
                            currency_code
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'KES')
                    """,
                    (
                        public_id,
                        provider_user_id,
                        job_id,
                        status_id,
                        gross_amount,
                        platform_fee_amount,
                        adjustment_amount,
                        net_amount,
                    ),
                )
                earning_id = cursor.lastrowid
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return {"id": int(earning_id), "public_id": public_id}

    def mark_available(self, earning_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                status_id = self._status_id(cursor, "AVAILABLE")
                cursor.execute(
                    """
                    UPDATE provider_earnings
                    SET status_id = %s,
                        available_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND status_id = (
                          SELECT id
                          FROM provider_earning_statuses
                          WHERE code = 'PENDING'
                          LIMIT 1
                      )
                    """,
                    (status_id, earning_id),
                )
                connection.commit()
                changed = cursor.rowcount > 0
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
            return changed
