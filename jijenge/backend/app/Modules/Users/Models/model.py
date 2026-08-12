from dataclasses import dataclass


@dataclass(frozen=True)
class UserProfile:
    user_id: int
    first_name: str
    last_name: str
    bio: str | None
    profile_photo_url: str | None
