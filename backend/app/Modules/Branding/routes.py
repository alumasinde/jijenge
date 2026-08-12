from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Branding.Controllers.branding_controller import BrandingController
from app.Modules.Branding.schema import BrandingResponse, BrandingUpdateRequest

router = APIRouter(prefix="/branding", tags=["Branding"])
controller = BrandingController()


@router.get("", response_model=BrandingResponse)
def get_branding():
    return controller.get_public()


@router.put("", response_model=BrandingResponse)
def update_branding(
    request: Request,
    data: BrandingUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    enforce_rate_limit(request, "branding:update", settings.auth_rate_limit_per_minute)
    return controller.update_default(data)
