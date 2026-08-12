from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Matching.Controllers.matching_controller import MatchingController
from app.Modules.Matching.schema import (
    MatchCandidateResponse,
    MatchLifecycleResponse,
    MatchRequest,
    MatchResponseRequest,
)

router = APIRouter(prefix="/matching", tags=["Matching"])
controller = MatchingController()


@router.post("/jobs/{job_id}/providers", response_model=list[MatchCandidateResponse])
def match_providers(
    request: Request,
    job_id: int,
    data: MatchRequest,
    current_user: AuthenticatedUser = Depends(require_role("CUSTOMER")),
):
    enforce_rate_limit(request, "matching:job-providers", settings.auth_rate_limit_per_minute)
    return controller.match_job(current_user.id, job_id, data.limit, data.refresh)


@router.get("/jobs/{job_id}/opportunity", response_model=MatchLifecycleResponse)
def view_match_opportunity(
    request: Request,
    job_id: int,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(request, "matching:view-opportunity", settings.auth_rate_limit_per_minute)
    return controller.view(current_user.id, job_id)


@router.post("/jobs/{job_id}/opportunity/respond", response_model=MatchLifecycleResponse)
def respond_to_match(
    request: Request,
    job_id: int,
    data: MatchResponseRequest,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(request, "matching:respond", settings.auth_rate_limit_per_minute)
    return controller.respond(current_user.id, job_id, data)
