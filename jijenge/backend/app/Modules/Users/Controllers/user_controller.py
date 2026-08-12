from app.Modules.Users.Services.user_service import UserService
from app.Modules.Users.schema import UpdateProfileRequest


class UserController:
    def __init__(self):
        self.service = UserService()

    def get_profile(self, user_id: int):
        return self.service.get_profile(user_id)

    def update_profile(self, user_id: int, data: UpdateProfileRequest):
        return self.service.update_profile(user_id, data)
