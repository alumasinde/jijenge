from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderProfile:
    id: int
    user_id: int
    status_code: str
    business_name: str | None
    professional_title: str | None
    bio: str | None
    years_experience: int | None
    is_verified: bool
