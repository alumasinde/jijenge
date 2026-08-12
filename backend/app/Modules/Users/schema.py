from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    bio: str | None = Field(default=None, max_length=5000)
    profile_photo_url: HttpUrl | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.strip().split())
        if not value:
            raise ValueError("Name is required")
        return value

    @field_validator("bio")
    @classmethod
    def clean_bio(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class UserProfileResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    bio: str | None
    profile_photo_url: str | None
