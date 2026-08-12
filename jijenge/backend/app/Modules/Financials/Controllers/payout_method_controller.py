import uuid
from fastapi import HTTPException

from app.database import db_connection


class PayoutMethodController:
    def create(self, user_id, method_type, account_name, account_reference):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT id FROM provider_profiles WHERE user_id=%s LIMIT 1",
                    (user_id,),
                )
                provider=cursor.fetchone()
                if not provider:
                    raise HTTPException(status_code=404,detail="Provider profile not found")

                cursor.execute(
                    """
                    SELECT id FROM provider_payout_method_types
                    WHERE code=%s AND is_active=1 LIMIT 1
                    """,
                    (method_type.upper(),),
                )
                mt=cursor.fetchone()
                if not mt:
                    raise HTTPException(status_code=422,detail="Unsupported payout method")

                cursor.execute(
                    """
                    INSERT INTO provider_payout_methods
                    (
                        public_id,provider_id,method_type_id,
                        account_name,account_reference
                    )
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        str(uuid.uuid4()),provider["id"],mt["id"],
                        account_name,account_reference,
                    ),
                )
                connection.commit()
                return {"id":cursor.lastrowid,"status":"PENDING_VERIFICATION"}
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def list(self,user_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ppm.id,ppm.public_id,ppmt.code AS method_type,
                    ppm.account_name,ppm.account_reference,
                    ppm.is_default,ppm.is_verified,ppm.is_active
                FROM provider_payout_methods ppm
                INNER JOIN provider_profiles pp ON pp.id=ppm.provider_id
                INNER JOIN provider_payout_method_types ppmt
                    ON ppmt.id=ppm.method_type_id
                WHERE pp.user_id=%s AND ppm.is_active=1
                ORDER BY ppm.is_default DESC,ppm.id DESC
                """,
                (user_id,),
            )
            rows=cursor.fetchall()
            cursor.close()
            return rows
