from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Auth.Controllers.auth_controller import AuthController
from app.Modules.Auth.schema import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
controller = AuthController()


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(request: Request, data: RegisterRequest):
    enforce_rate_limit(
        request, "auth:register", settings.register_rate_limit_per_minute
    )
    return controller.register(request, data)


@router.post("/login", response_model=AuthResponse)
def login(request: Request, data: LoginRequest):
    enforce_rate_limit(
        request, "auth:login", settings.login_rate_limit_per_minute
    )
    return controller.login(request, data)


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, data: RefreshRequest):
    enforce_rate_limit(
        request, "auth:refresh", settings.refresh_rate_limit_per_minute
    )
    return controller.refresh(request, data)


@router.post("/logout")
def logout(request: Request, data: LogoutRequest):
    enforce_rate_limit(
        request, "auth:logout", settings.auth_rate_limit_per_minute
    )
    return controller.logout(request, data)


@router.get("/me")
def me(current_user: AuthenticatedUser = Depends(require_active_user)):
    service = AuthController().service
    user = service.repository.get_auth_user(current_user.id)
    return service._user_response(user)
