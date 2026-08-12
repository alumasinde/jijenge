from datetime import datetime, timezone
import re

from fastapi import HTTPException, status

from app.Core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    new_token_version,
    verify_password,
)
from app.Modules.Auth.Repositories.auth_repository import AuthRepository
from app.Modules.Auth.schema import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
)


_PHONE_RE = re.compile(r"^[0-9+() .-]{7,32}$")


class AuthService:
    def __init__(self):
        self.repository = AuthRepository()

    def _validate_identifier(self, identifier: str) -> str:
        identifier = identifier.strip().lower()
        if not identifier:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return identifier

    def _user_response(self, user: dict) -> UserResponse:
        return UserResponse(
            id=int(user["id"]),
            email=user["email"],
            phone=user["phone"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            status=user["status_code"],
            roles=user["roles"],
        )

    def register(self, data: RegisterRequest) -> AuthResponse:
        email = str(data.email).lower() if data.email else None
        phone = data.phone.strip() if data.phone else None

        if not email and not phone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email or phone is required",
            )

        if phone and not _PHONE_RE.fullmatch(phone):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid phone format",
            )

        if self.repository.email_or_phone_exists(email, phone):
            # Avoid revealing which credential is already registered.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with those credentials already exists",
            )

        token_version = new_token_version()
        password_hash = hash_password(data.password)

        try:
            result = self.repository.create_user(
                first_name=data.first_name,
                last_name=data.last_name,
                email=email,
                phone=phone,
                password_hash=password_hash,
                token_version=token_version,
            )
        except Exception as exc:
            message = str(exc).lower()
            if "duplicate" in message or "uq_users_" in message:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with those credentials already exists",
                )
            raise

        user = self.repository.get_auth_user(int(result["id"]))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account creation failed",
            )

        access_token = create_access_token(user["id"], token_version)
        refresh_token, refresh_jti = create_refresh_token(
            user["id"], token_version
        )
        self.repository.save_refresh_token(
            user["id"], refresh_token, refresh_jti, token_version
        )

        return AuthResponse(
            user=self._user_response(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def login(self, data: LoginRequest) -> AuthResponse:
        identifier = self._validate_identifier(data.identifier)
        user = self.repository.get_auth_user_by_identifier(identifier)

        # Perform password verification even when the user does not exist
        # to reduce obvious timing differences.
        valid_password = verify_password(
            data.password,
            user["password_hash"] if user else "$argon2id$v=19$m=65536,t=3,p=4$invalid$invalid",
        )

        if not user or not valid_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if user["status_code"] != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active",
            )

        self.repository.update_last_login(user["id"])

        access_token = create_access_token(
            user["id"], user["token_version"]
        )
        refresh_token, refresh_jti = create_refresh_token(
            user["id"], user["token_version"]
        )
        self.repository.save_refresh_token(
            user["id"],
            refresh_token,
            refresh_jti,
            user["token_version"],
        )

        return AuthResponse(
            user=self._user_response(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh(self, data: RefreshRequest) -> AuthResponse:
        try:
            payload = decode_token(data.refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        stored = self.repository.get_refresh_token(data.refresh_token)
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if stored["revoked_at"] is not None:
            # Reuse of a rotated refresh token is treated as a possible
            # token theft event: revoke the user's remaining sessions.
            self.repository.revoke_all_refresh_tokens(stored["user_id"])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has already been used",
            )

        expires_at = stored["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= datetime.now(timezone.utc):
            self.repository.revoke_refresh_token(data.refresh_token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        if stored["token_jti"] != payload.get("jti"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = self.repository.get_auth_user(stored["user_id"])
        if not user or user["status_code"] != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User session is not active",
            )

        if stored["token_version"] != user["token_version"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked",
            )

        access_token = create_access_token(
            user["id"], user["token_version"]
        )
        new_refresh, new_jti = create_refresh_token(
            user["id"], user["token_version"]
        )
        new_id = self.repository.save_refresh_token(
            user["id"],
            new_refresh,
            new_jti,
            user["token_version"],
        )
        self.repository.revoke_refresh_token(
            data.refresh_token,
            replaced_by_token_id=new_id,
        )

        return AuthResponse(
            user=self._user_response(user),
            access_token=access_token,
            refresh_token=new_refresh,
        )

    def logout(self, data: LogoutRequest) -> dict:
        self.repository.revoke_refresh_token(data.refresh_token)
        return {"success": True, "message": "Logged out successfully"}
