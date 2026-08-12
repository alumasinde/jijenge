from fastapi import APIRouter, Depends, Query, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Providers.Controllers.provider_controller import ProviderController
from app.Modules.Providers.schema import (
    AddProviderServiceRequest,
    ProviderDiscoveryResponse,
    ProviderOnboardingRequest,
    ProviderProfileResponse,
    ProviderServiceResponse,
)

router = APIRouter(prefix="/providers", tags=["Providers"])
controller = ProviderController()


@router.post("/me/onboarding", response_model=ProviderProfileResponse, status_code=201)
def onboard(
    request: Request,
    data: ProviderOnboardingRequest,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(request, "providers:onboarding", settings.auth_rate_limit_per_minute)
    return controller.onboard(current_user.id, data)


@router.get("/me", response_model=ProviderProfileResponse)
def get_me(current_user: AuthenticatedUser = Depends(require_active_user)):
    return controller.get_profile(current_user.id)


@router.patch("/me", response_model=ProviderProfileResponse)
def update_me(
    request: Request,
    data: ProviderOnboardingRequest,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(request, "providers:update", settings.auth_rate_limit_per_minute)
    return controller.update_profile(current_user.id, data)


@router.post("/me/services", response_model=ProviderServiceResponse)
def add_service(
    request: Request,
    data: AddProviderServiceRequest,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(request, "providers:add-service", settings.auth_rate_limit_per_minute)
    return controller.add_service(current_user.id, data)


@router.get("/me/services", response_model=list[ProviderServiceResponse])
def list_services(current_user: AuthenticatedUser = Depends(require_active_user)):
    return controller.list_services(current_user.id)


@router.get("/discover", response_model=list[ProviderDiscoveryResponse])
def discover(
    service_id: int | None = Query(default=None, ge=1),
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=20, gt=0, le=500),
    limit: int = Query(default=20, ge=1, le=100),
    verified_only: bool = False,
):
    return controller.discover(
        service_id, latitude, longitude, radius_km, limit, verified_only
    )
