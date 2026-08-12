from datetime import timedelta
import uuid

from fastapi import HTTPException

from app.database import db_connection


class HoldService:
    def create_default_hold(self, provider_earning_id, service_category_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                connection.start_transaction()

                cursor.execute(
                    """
                    SELECT id,provider_id,assignment_id
                    FROM provider_earnings
                    WHERE id=%s
                    FOR UPDATE
                    """,
                    (provider_earning_id,),
                )
                earning = cursor.fetchone()
                if not earning:
                    raise HTTPException(status_code=404, detail="Provider earning not found")

                cursor.execute(
                    """
                    SELECT hold_hours
                    FROM settlement_hold_rules
                    WHERE is_active=1
                      AND (
                            service_category_id=%s
                            OR (service_category_id IS NULL AND is_default=1)
                          )
                    ORDER BY
                        CASE WHEN service_category_id=%s THEN 1 ELSE 2 END,
                        id DESC
                    LIMIT 1
                    """,
                    (service_category_id, service_category_id),
                )
                rule = cursor.fetchone()
                if not rule:
                    raise HTTPException(status_code=409, detail="No settlement hold rule configured")

                cursor.execute(
                    """
                    SELECT id
                    FROM provider_earning_hold_reasons
                    WHERE code='DISPUTE_WINDOW'
                    LIMIT 1
                    """
                )
                reason = cursor.fetchone()["id"]

                cursor.execute(
                    """
                    INSERT INTO provider_earning_holds
                        (
                            provider_earning_id,hold_reason_id,
                            starts_at,releases_at
                        )
                    VALUES
                        (
                            %s,%s,CURRENT_TIMESTAMP,
                            DATE_ADD(CURRENT_TIMESTAMP,INTERVAL %s HOUR)
                        )
                    """,
                    (provider_earning_id, reason, int(rule["hold_hours"])),
                )

                cursor.execute(
                    """
                    UPDATE provider_earnings
                    SET status_id=(
                        SELECT id FROM provider_earning_statuses
                        WHERE code='ON_HOLD' LIMIT 1
                    ),
                    available_at=NULL,
                    updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                    """,
                    (provider_earning_id,),
                )

                connection.commit()
                return {
                    "provider_earning_id": provider_earning_id,
                    "hold_hours": int(rule["hold_hours"]),
                }
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
