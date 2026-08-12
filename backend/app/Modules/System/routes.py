from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.database import db_connection
from app.Modules.System.Controllers.system_controller import SystemController
from app.Modules.System.schema import SystemSettingResponse, SystemSettingUpsertRequest

router = APIRouter(prefix="/system", tags=["System"])
controller = SystemController()
SettingKey = Annotated[str, Path(min_length=2, max_length=150, pattern=r"^[a-z0-9][a-z0-9_.-]*$")]


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def readiness():
    try:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        return {"status": "ready", "database": "ok"}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service is not ready")


@router.get("/settings", response_model=list[SystemSettingResponse])
def public_settings():
    return controller.public_settings()


@router.get("/settings/{setting_key}", response_model=SystemSettingResponse)
def public_setting(setting_key: SettingKey):
    return controller.get_public_setting(setting_key)


@router.get("/admin/settings", response_model=list[SystemSettingResponse])
def admin_settings(
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    return controller.all_settings()


@router.put("/admin/settings/{setting_key}", response_model=SystemSettingResponse)
def upsert_setting(
    request: Request,
    setting_key: SettingKey,
    data: SystemSettingUpsertRequest,
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    enforce_rate_limit(request, "system:settings:update", settings.auth_rate_limit_per_minute)
    return controller.upsert(setting_key, data)


@router.delete("/admin/settings/{setting_key}")
def delete_setting(
    request: Request,
    setting_key: SettingKey,
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    enforce_rate_limit(request, "system:settings:delete", settings.auth_rate_limit_per_minute)
    return controller.delete(setting_key)
