from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request, HTTPException

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Availability.Controllers.availability_controller import (
    AvailabilityController,
)
from app.Modules.Availability.schema import (
    AvailabilityExceptionRequest,
    AvailabilityExceptionResponse,
    AvailabilityRuleRequest,
    AvailabilityRuleResponse,
    MatchingPreferencesRequest,
    MatchingPreferencesResponse,
)
from app.Modules.Providers.Repositories.provider_repository import ProviderRepository

router = APIRouter(prefix="/availability", tags=["Availability"])
controller = AvailabilityController()


def provider_id_for_user(user_id: int) -> int:
    profile = ProviderRepository().get_profile_by_user(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Provider profile not found")
    return int(profile["id"])


@router.post("/rules", response_model=AvailabilityRuleResponse, status_code=201)
def add_rule(
    request: Request,
    data: AvailabilityRuleRequest,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "availability:add-rule",
        settings.auth_rate_limit_per_minute,
    )
    return controller.add_rule(provider_id_for_user(current_user.id), data)


@router.get("/rules", response_model=list[AvailabilityRuleResponse])
def list_rules(
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    return controller.list_rules(provider_id_for_user(current_user.id))


@router.post(
    "/exceptions",
    response_model=AvailabilityExceptionResponse,
    status_code=201,
)
def add_exception(
    request: Request,
    data: AvailabilityExceptionRequest,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "availability:add-exception",
        settings.auth_rate_limit_per_minute,
    )
    return controller.add_exception(
        provider_id_for_user(current_user.id), data
    )


@router.get(
    "/exceptions",
    response_model=list[AvailabilityExceptionResponse],
)
def list_exceptions(
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
    from_date: date | None = None,
    to_date: date | None = None,
):
    from_date = from_date or date.today()
    to_date = to_date or (from_date + timedelta(days=30))
    if to_date < from_date:
        raise HTTPException(status_code=422, detail="Invalid date range")
    if (to_date - from_date).days > 366:
        raise HTTPException(status_code=422, detail="Date range is too large")
    return controller.list_exceptions(
        provider_id_for_user(current_user.id),
        from_date,
        to_date,
    )


@router.put(
    "/matching-preferences",
    response_model=MatchingPreferencesResponse,
)
def update_matching_preferences(
    request: Request,
    data: MatchingPreferencesRequest,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "availability:matching-preferences",
        settings.auth_rate_limit_per_minute,
    )
    return controller.upsert_preferences(
        provider_id_for_user(current_user.id), data
    )


@router.get(
    "/matching-preferences",
    response_model=MatchingPreferencesResponse | None,
)
def get_matching_preferences(
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    return controller.get_preferences(
        provider_id_for_user(current_user.id)
    )
