from fastapi import APIRouter, Depends, Query, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Reviews.Controllers.review_controller import ReviewController
from app.Modules.Reviews.schema import (
    CreateReviewRequest,
    ProviderRatingResponse,
    ReviewResponse,
)

router = APIRouter(prefix="/reviews", tags=["Reviews"])
controller = ReviewController()


@router.post(
    "/jobs/{job_id}",
    response_model=ReviewResponse,
    status_code=201,
)
def create_review(
    request: Request,
    job_id: int,
    data: CreateReviewRequest,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request,
        "reviews:create",
        settings.auth_rate_limit_per_minute,
    )
    return controller.create(current_user.id, job_id, data)


@router.get("/me", response_model=list[ReviewResponse])
def my_reviews(
    current_user: AuthenticatedUser = Depends(require_active_user),
    limit: int = Query(default=20, ge=1, le=100),
):
    return controller.list_for_user(current_user.id, limit)


@router.get(
    "/providers/{provider_user_id}/summary",
    response_model=ProviderRatingResponse,
)
def provider_rating_summary(provider_user_id: int):
    return controller.provider_summary(provider_user_id)
