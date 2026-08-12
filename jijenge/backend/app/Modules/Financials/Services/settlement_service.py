import uuid
from fastapi import HTTPException

from app.database import db_connection


class SettlementService:
    def _provider_id_from_user(self, cursor, user_id):
        cursor.execute(
            "SELECT id FROM provider_profiles WHERE user_id=%s LIMIT 1",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        return int(row["id"])

    def request(self, provider_user_id, earning_id, idempotency_key, payout_method_id=None):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                provider_id = self._provider_id_from_user(cursor, provider_user_id)

                cursor.execute(
                    """
                    SELECT
                        pe.id, pe.provider_id, pe.assignment_id, pe.net_amount,
                        pe.currency_code, pes.code AS earning_status
                    FROM provider_earnings pe
                    INNER JOIN provider_earning_statuses pes ON pes.id=pe.status_id
                    WHERE pe.id=%s AND pe.provider_id=%s
                    FOR UPDATE
                    """,
                    (earning_id, provider_id),
                )
                earning = cursor.fetchone()
                if not earning:
                    raise HTTPException(status_code=404, detail="Provider earning not found")
                if earning["earning_status"] != "AVAILABLE":
                    raise HTTPException(
                        status_code=409,
                        detail="This earning is not available for settlement",
                    )

                if payout_method_id:
                    cursor.execute(
                        """
                        SELECT id
                        FROM provider_payout_methods
                        WHERE id=%s AND provider_id=%s
                          AND is_active=1 AND is_verified=1
                        LIMIT 1
                        """,
                        (payout_method_id, provider_id),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id
                        FROM provider_payout_methods
                        WHERE provider_id=%s AND is_active=1 AND is_verified=1
                        ORDER BY is_default DESC,id DESC
                        LIMIT 1
                        """,
                        (provider_id,),
                    )
                payout_method = cursor.fetchone()
                if not payout_method:
                    raise HTTPException(
                        status_code=409,
                        detail="A verified provider payout method is required",
                    )

                cursor.execute(
                    """
                    SELECT *
                    FROM provider_settlements
                    WHERE provider_id=%s AND idempotency_key=%s
                    LIMIT 1
                    """,
                    (provider_id, idempotency_key),
                )
                existing = cursor.fetchone()
                if existing:
                    connection.commit()
                    cursor.close()
                    return existing

                cursor.execute(
                    """
                    SELECT id
                    FROM provider_settlement_statuses
                    WHERE code='REQUESTED'
                    LIMIT 1
                    """
                )
                requested_status = cursor.fetchone()["id"]

                cursor.execute(
                    """
                    INSERT INTO provider_settlements
                    (
                        public_id,provider_id,assignment_id,
                        provider_earning_id,status_id,amount,
                        currency_code,provider_payout_method_id,
                        idempotency_key,requested_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
                    """,
                    (
                        str(uuid.uuid4()), provider_id, earning["assignment_id"],
                        earning_id, requested_status, earning["net_amount"],
                        earning["currency_code"], payout_method["id"],
                        idempotency_key,
                    ),
                )
                settlement_id = int(cursor.lastrowid)

                cursor.execute(
                    """
                    UPDATE provider_earnings
                    SET status_id=(
                        SELECT id FROM provider_earning_statuses
                        WHERE code='ON_HOLD' LIMIT 1
                    ),
                    updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,
                    (earning_id,),
                )

                cursor.execute(
                    """
                    INSERT INTO provider_payout_events
                        (settlement_id,event_type_id,actor_user_id,notes)
                    SELECT %s,id,%s,'Provider requested settlement'
                    FROM provider_payout_event_types
                    WHERE code='REQUESTED'
                    LIMIT 1
                    """,
                    (settlement_id, provider_user_id),
                )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return self.get(provider_user_id, settlement_id)

    def get(self, provider_user_id, settlement_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            provider_id = self._provider_id_from_user(cursor, provider_user_id)
            cursor.execute(
                """
                SELECT
                    ps.id,ps.public_id,ps.assignment_id,ps.provider_earning_id,
                    ps.amount,ps.currency_code,
                    pss.code AS status,
                    ps.payout_reference,ps.requested_at,
                    ps.processing_at,ps.paid_at,ps.failure_reason,
                    ppm.public_id AS payout_method_public_id,
                    ppmt.code AS payout_method
                FROM provider_settlements ps
                INNER JOIN provider_settlement_statuses pss
                    ON pss.id=ps.status_id
                LEFT JOIN provider_payout_methods ppm
                    ON ppm.id=ps.provider_payout_method_id
                LEFT JOIN provider_payout_method_types ppmt
                    ON ppmt.id=ppm.method_type_id
                WHERE ps.id=%s AND ps.provider_id=%s
                LIMIT 1
                """,
                (settlement_id, provider_id),
            )
            row = cursor.fetchone()
            cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Settlement not found")
        return row

    def release_expired_holds(self, limit=100):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()

                cursor.execute(
                    """
                    SELECT
                        peh.id AS hold_id,
                        peh.provider_earning_id,
                        pe.id AS earning_id
                    FROM provider_earning_holds peh
                    INNER JOIN provider_earnings pe
                        ON pe.id=peh.provider_earning_id
                    INNER JOIN provider_earning_statuses pes
                        ON pes.id=pe.status_id
                    WHERE peh.released_at IS NULL
                      AND peh.releases_at IS NOT NULL
                      AND peh.releases_at <= CURRENT_TIMESTAMP
                      AND pes.code='ON_HOLD'
                    ORDER BY peh.id
                    LIMIT %s
                    FOR UPDATE
                    """,
                    (limit,),
                )
                holds = cursor.fetchall()

                for hold in holds:
                    cursor.execute(
                        """
                        SELECT id FROM provider_earning_statuses
                        WHERE code='AVAILABLE' LIMIT 1
                        """
                    )
                    available = cursor.fetchone()["id"]
                    cursor.execute(
                        """
                        UPDATE provider_earnings
                        SET status_id=%s,available_at=CURRENT_TIMESTAMP,
                            updated_at=CURRENT_TIMESTAMP
                        WHERE id=%s
                        """,
                        (available, hold["earning_id"]),
                    )
                    cursor.execute(
                        """
                        UPDATE provider_earning_holds
                        SET released_at=CURRENT_TIMESTAMP,
                            updated_at=CURRENT_TIMESTAMP
                        WHERE id=%s
                        """,
                        (hold["hold_id"],),
                    )

                connection.commit()
                return len(holds)
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
