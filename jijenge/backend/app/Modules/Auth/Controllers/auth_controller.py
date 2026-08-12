from fastapi import Request

from app.Modules.Auth.Services.auth_service import AuthService
from app.Modules.Auth.schema import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
)


class AuthController:
    def __init__(self):
        self.service = AuthService()

    def register(self, request: Request, data: RegisterRequest) -> AuthResponse:
        return self.service.register(data)

    def login(self, request: Request, data: LoginRequest) -> AuthResponse:
        return self.service.login(data)

    def refresh(self, request: Request, data: RefreshRequest) -> AuthResponse:
        return self.service.refresh(data)

    def logout(self, request: Request, data: LogoutRequest) -> dict:
        return self.service.logout(data)
