from fastapi import APIRouter, Depends, Query, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Locations.Controllers.location_controller import LocationController
from app.Modules.Locations.schema import (
    NearbyProviderResponse,
    ProviderLocationRequest,
    ProviderLocationResponse,
    ServiceAreaRequest,
    ServiceAreaResponse,
)

router = APIRouter(prefix="/locations", tags=["Locations"])
controller = LocationController()


@router.post(
    "/providers/me/locations",
    response_model=ProviderLocationResponse,
    status_code=201,
)
def set_provider_location(
    request: Request,
    data: ProviderLocationRequest,
    current_user: AuthenticatedUser = Depends(
        require_role("PROVIDER")
    ),
):
    enforce_rate_limit(
        request, "locations:provider-location",
        settings.auth_rate_limit_per_minute
    )
    # The provider ID is resolved by the service/repository layer from the
    # authenticated account in the next provider-aware implementation.
    from app.Modules.Providers.Repositories.provider_repository import ProviderRepository
    profile = ProviderRepository().get_profile_by_user(current_user.id)
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Provider profile not found")
    return controller.set_provider_location(int(profile["id"]), data)


@router.get(
    "/providers/me/locations",
    response_model=list[ProviderLocationResponse],
)
def list_provider_locations(
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    from app.Modules.Providers.Repositories.provider_repository import ProviderRepository
    profile = ProviderRepository().get_profile_by_user(current_user.id)
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Provider profile not found")
    return controller.list_provider_locations(int(profile["id"]))


@router.post(
    "/providers/me/service-areas",
    response_model=ServiceAreaResponse,
    status_code=201,
)
def add_service_area(
    request: Request,
    data: ServiceAreaRequest,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "locations:service-area",
        settings.auth_rate_limit_per_minute
    )
    from app.Modules.Providers.Repositories.provider_repository import ProviderRepository
    profile = ProviderRepository().get_profile_by_user(current_user.id)
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Provider profile not found")
    return controller.add_service_area(int(profile["id"]), data)


@router.get(
    "/providers/me/service-areas",
    response_model=list[ServiceAreaResponse],
)
def list_service_areas(
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    from app.Modules.Providers.Repositories.provider_repository import ProviderRepository
    profile = ProviderRepository().get_profile_by_user(current_user.id)
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Provider profile not found")
    return controller.list_service_areas(int(profile["id"]))


@router.get(
    "/nearby-providers",
    response_model=list[NearbyProviderResponse],
)
def nearby_providers(
    service_id: int = Query(ge=1),
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=10, gt=0, le=500),
    limit: int = Query(default=20, ge=1, le=100),
):
    return controller.nearby_providers(
        service_id, latitude, longitude, radius_km, limit
    )


@router.get(
    "/nearby-providers/by-service-area",
    response_model=list[NearbyProviderResponse],
)
def nearby_providers_by_service_area(
    service_id: int = Query(ge=1),
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    limit: int = Query(default=20, ge=1, le=100),
):
    return controller.nearby_providers_by_service_area(
        service_id, latitude, longitude, limit
    )
