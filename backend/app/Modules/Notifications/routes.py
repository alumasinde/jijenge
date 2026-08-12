from fastapi import APIRouter, Depends, Query, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Notifications.Controllers.notification_controller import NotificationController
from app.Modules.Notifications.schema import (
    MarkReadResponse,
    NotificationListResponse,
    RegisterDeviceTokenRequest,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])
controller = NotificationController()


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    current_user: AuthenticatedUser = Depends(require_active_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
):
    return controller.list_for_user(current_user.id, limit, offset)


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
def mark_notification_read(
    request: Request,
    notification_id: int,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request, "notifications:read", settings.auth_rate_limit_per_minute
    )
    return controller.mark_read(current_user.id, notification_id)


@router.post("/read-all", response_model=MarkReadResponse)
def mark_all_notifications_read(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request, "notifications:read-all", settings.auth_rate_limit_per_minute
    )
    return controller.mark_all_read(current_user.id)


@router.post("/devices")
def register_device(
    request: Request,
    data: RegisterDeviceTokenRequest,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request, "notifications:device-register", settings.auth_rate_limit_per_minute
    )
    return controller.register_device(current_user.id, data)


@router.delete("/devices/{token}")
def deactivate_device(
    request: Request,
    token: str,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request, "notifications:device-delete", settings.auth_rate_limit_per_minute
    )
    return controller.deactivate_device(current_user.id, token)
