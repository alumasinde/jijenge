from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProviderOnboardingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_name: str | None = Field(default=None, max_length=180)
    professional_title: str | None = Field(default=None, max_length=180)
    bio: str | None = Field(default=None, max_length=5000)
    years_experience: int | None = Field(default=None, ge=0, le=80)

    @field_validator("business_name", "professional_title")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.strip().split())
        return value or None

    @field_validator("bio")
    @classmethod
    def clean_bio(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ProviderProfileResponse(BaseModel):
    id: int
    user_id: int
    status: str
    business_name: str | None
    professional_title: str | None
    bio: str | None
    years_experience: int | None
    is_verified: bool


class AddProviderServiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_id: int = Field(ge=1)
    years_experience: int | None = Field(default=None, ge=0, le=80)
    minimum_price: Decimal | None = Field(default=None, ge=0)
    maximum_price: Decimal | None = Field(default=None, ge=0)

    @field_validator("maximum_price")
    @classmethod
    def validate_price_range(cls, value, info):
        minimum = info.data.get("minimum_price")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("maximum_price must be greater than or equal to minimum_price")
        return value


class ProviderServiceResponse(BaseModel):
    service_id: int
    service_code: str
    service_name: str
    years_experience: int | None
    minimum_price: Decimal | None
    maximum_price: Decimal | None
    is_active: bool


class ProviderDiscoveryResponse(BaseModel):
    provider_id: int
    business_name: str | None
    professional_title: str | None
    bio: str | None
    years_experience: int | None
    is_verified: bool
    distance_km: float
    services: list[str]
