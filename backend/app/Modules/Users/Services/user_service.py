from fastapi import HTTPException, status

from app.Modules.Users.Repositories.user_repository import UserRepository
from app.Modules.Users.schema import UpdateProfileRequest, UserProfileResponse


class UserService:
    def __init__(self):
        self.repository = UserRepository()

    def get_profile(self, user_id: int) -> UserProfileResponse:
        profile = self.repository.get_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )
        return UserProfileResponse(
            id=int(profile["user_id"]),
            first_name=profile["first_name"],
            last_name=profile["last_name"],
            bio=profile["bio"],
            profile_photo_url=profile["profile_photo_url"],
        )

    def update_profile(
        self, user_id: int, data: UpdateProfileRequest
    ) -> UserProfileResponse:
        profile = self.repository.update_profile(
            user_id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            bio=data.bio,
            profile_photo_url=(
                str(data.profile_photo_url)
                if data.profile_photo_url
                else None
            ),
        )
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )
        return self.get_profile(user_id)
