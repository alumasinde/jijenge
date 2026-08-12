import hashlib
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.database import db_connection
from app.Modules.Auth.Models.model import AuthUser


class AuthRepository:
    def get_auth_user_by_identifier(self, identifier: str) -> dict | None:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    u.id,
                    u.email,
                    u.phone,
                    u.password_hash,
                    us.code AS status_code,
                    u.token_version,
                    up.first_name,
                    up.last_name
                FROM users u
                INNER JOIN user_statuses us ON us.id = u.status_id
                INNER JOIN user_profiles up ON up.user_id = u.id
                WHERE u.deleted_at IS NULL
                  AND (u.email = %s OR u.phone = %s)
                LIMIT 1
                """,
                (identifier, identifier),
            )
            user = cursor.fetchone()

            if not user:
                cursor.close()
                return None

            cursor.execute(
                """
                SELECT r.code
                FROM user_roles ur
                INNER JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                  AND r.is_active = 1
                ORDER BY r.id
                """,
                (user["id"],),
            )
            user["roles"] = [row["code"] for row in cursor.fetchall()]
            cursor.close()
            return user

    def get_auth_user(self, user_id: int) -> dict | None:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    u.id,
                    u.email,
                    u.phone,
                    u.password_hash,
                    us.code AS status_code,
                    u.token_version,
                    up.first_name,
                    up.last_name
                FROM users u
                INNER JOIN user_statuses us ON us.id = u.status_id
                INNER JOIN user_profiles up ON up.user_id = u.id
                WHERE u.id = %s
                  AND u.deleted_at IS NULL
                LIMIT 1
                """,
                (user_id,),
            )
            user = cursor.fetchone()

            if not user:
                cursor.close()
                return None

            cursor.execute(
                """
                SELECT r.code
                FROM user_roles ur
                INNER JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                  AND r.is_active = 1
                ORDER BY r.id
                """,
                (user_id,),
            )
            user["roles"] = [row["code"] for row in cursor.fetchall()]
            cursor.close()
            return user

    def user_has_role(self, user_id: int, role_code: str) -> bool:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM user_roles ur
                INNER JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                  AND r.code = %s
                  AND r.is_active = 1
                LIMIT 1
                """,
                (user_id, role_code),
            )
            result = cursor.fetchone()
            cursor.close()
            return result is not None

    def email_or_phone_exists(self, email: str | None, phone: str | None) -> bool:
        if not email and not phone:
            return False

        with db_connection() as connection:
            cursor = connection.cursor()
            if email and phone:
                cursor.execute(
                    "SELECT id FROM users WHERE deleted_at IS NULL AND (email = %s OR phone = %s) LIMIT 1",
                    (email, phone),
                )
            elif email:
                cursor.execute(
                    "SELECT id FROM users WHERE deleted_at IS NULL AND email = %s LIMIT 1",
                    (email,),
                )
            else:
                cursor.execute(
                    "SELECT id FROM users WHERE deleted_at IS NULL AND phone = %s LIMIT 1",
                    (phone,),
                )
            result = cursor.fetchone()
            cursor.close()
            return result is not None

    def create_user(
        self,
        first_name: str,
        last_name: str,
        email: str | None,
        phone: str | None,
        password_hash: str,
        token_version: str,
    ) -> dict:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT id FROM user_statuses WHERE code = 'ACTIVE' LIMIT 1"
                )
                status = cursor.fetchone()
                if not status:
                    raise RuntimeError("ACTIVE user status is missing")

                cursor.execute(
                    "SELECT id FROM roles WHERE code = 'CUSTOMER' AND is_active = 1 LIMIT 1"
                )
                role = cursor.fetchone()
                if not role:
                    raise RuntimeError("CUSTOMER role is missing")

                cursor.execute(
                    """
                    INSERT INTO users
                        (email, phone, password_hash, status_id, token_version)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (email, phone, password_hash, status["id"], token_version),
                )
                user_id = cursor.lastrowid

                cursor.execute(
                    """
                    INSERT INTO user_profiles
                        (user_id, first_name, last_name)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, first_name, last_name),
                )

                cursor.execute(
                    """
                    INSERT INTO user_roles
                        (user_id, role_id)
                    VALUES (%s, %s)
                    """,
                    (user_id, role["id"]),
                )

                connection.commit()
                return {"id": int(user_id)}
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def update_last_login(self, user_id: int) -> None:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s",
                (user_id,),
            )
            connection.commit()
            cursor.close()

    def save_refresh_token(
        self,
        user_id: int,
        token: str,
        token_jti: str,
        token_version: str,
    ) -> int:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO refresh_tokens
                    (user_id, token_hash, token_jti, token_version, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, token_hash, token_jti, token_version, expires_at),
            )
            token_id = cursor.lastrowid
            connection.commit()
            cursor.close()
            return int(token_id)

    def get_refresh_token(self, token: str) -> dict | None:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id, user_id, token_hash, token_jti,
                    token_version, expires_at, revoked_at
                FROM refresh_tokens
                WHERE token_hash = %s
                LIMIT 1
                """,
                (token_hash,),
            )
            result = cursor.fetchone()
            cursor.close()
            return result

    def revoke_refresh_token(self, token: str, replaced_by_token_id: int | None = None) -> None:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE refresh_tokens
                SET revoked_at = CURRENT_TIMESTAMP,
                    replaced_by_token_id = COALESCE(%s, replaced_by_token_id)
                WHERE token_hash = %s
                  AND revoked_at IS NULL
                """,
                (replaced_by_token_id, token_hash),
            )
            connection.commit()
            cursor.close()

    def revoke_all_refresh_tokens(self, user_id: int) -> None:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE refresh_tokens
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                  AND revoked_at IS NULL
                """,
                (user_id,),
            )
            cursor.execute(
                """
                UPDATE users
                SET token_version = REPLACE(UUID(), '-', '')
                WHERE id = %s
                """,
                (user_id,),
            )
            connection.commit()
            cursor.close()
