import hashlib
import hmac
import time

from fastapi import HTTPException, Request, status

from app.config import settings
from app.database import db_connection


class RateLimiter:
    """
    MySQL-backed fixed-window limiter.
    It works across multiple FastAPI workers/instances because state is stored in MySQL.
    """

    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds

    def _hash_key(self, raw_key: str) -> str:
        return hmac.new(
            settings.jwt_secret.encode("utf-8"),
            raw_key.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def check(self, raw_key: str) -> tuple[bool, int]:
        if not settings.rate_limit_enabled:
            return True, self.limit

        now = int(time.time())
        window_start = now - (now % self.window_seconds)
        key_hash = self._hash_key(raw_key)

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                INSERT INTO rate_limit_buckets
                    (key_hash, window_start, request_count, expires_at)
                VALUES
                    (%s, %s, 1, FROM_UNIXTIME(%s + %s))
                ON DUPLICATE KEY UPDATE
                    request_count = IF(
                        window_start = VALUES(window_start),
                        request_count + 1,
                        1
                    ),
                    window_start = VALUES(window_start),
                    expires_at = VALUES(expires_at)
                """,
                (
                    key_hash,
                    window_start,
                    window_start,
                    self.window_seconds,
                ),
            )

            cursor.execute(
                """
                SELECT request_count
                FROM rate_limit_buckets
                WHERE key_hash = %s
                  AND window_start = %s
                FOR UPDATE
                """,
                (key_hash, window_start),
            )
            row = cursor.fetchone()
            connection.commit()
            cursor.close()

        count = int(row["request_count"]) if row else self.limit + 1
        remaining = max(self.limit - count, 0)

        if count > self.limit:
            return False, remaining

        return True, remaining


def client_ip(request: Request) -> str:
    # Deliberately use the socket peer address. Do not trust X-Forwarded-For
    # until a trusted reverse-proxy configuration is explicitly introduced.
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(request: Request, bucket: str, limit: int) -> None:
    allowed, remaining = RateLimiter(limit).check(
        f"{bucket}:ip:{client_ip(request)}"
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Remaining": "0",
            },
        )
