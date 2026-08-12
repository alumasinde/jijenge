from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Users.Controllers.user_controller import UserController
from app.Modules.Users.schema import UpdateProfileRequest, UserProfileResponse

router = APIRouter(prefix="/users", tags=["Users"])
controller = UserController()


@router.get("/me/profile", response_model=UserProfileResponse)
def get_profile(
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    return controller.get_profile(current_user.id)


@router.patch("/me/profile", response_model=UserProfileResponse)
def update_profile(
    request: Request,
    data: UpdateProfileRequest,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request, "users:update-profile", settings.auth_rate_limit_per_minute
    )
    return controller.update_profile(current_user.id, data)
