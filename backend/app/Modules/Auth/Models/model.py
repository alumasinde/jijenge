from dataclasses import dataclass


@dataclass(frozen=True)
class AuthUser:
    id: int
    email: str | None
    phone: str | None
    password_hash: str
    status_code: str
    token_version: str
    first_name: str
    last_name: str
    roles: list[str]
