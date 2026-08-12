from pydantic import BaseModel, ConfigDict, Field, field_validator


class CoordinatesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ProviderLocationRequest(CoordinatesRequest):
    address_line: str | None = Field(default=None, max_length=500)
    accuracy_meters: float | None = Field(default=None, ge=0, le=100000)
    is_primary: bool = True

    @field_validator("address_line")
    @classmethod
    def clean_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.strip().split())
        return value or None


class ProviderLocationResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    address_line: str | None
    accuracy_meters: float | None
    is_primary: bool
    is_active: bool


class ServiceAreaRequest(CoordinatesRequest):
    radius_km: float = Field(default=10, gt=0, le=500)
    name: str | None = Field(default=None, max_length=180)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.strip().split())
        return value or None


class ServiceAreaResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    radius_km: float
    name: str | None
    is_active: bool


class NearbyProviderResponse(BaseModel):
    provider_id: int
    distance_km: float
    business_name: str | None
    professional_title: str | None
    is_verified: bool


class JobLocationRequest(CoordinatesRequest):
    address_line: str | None = Field(default=None, max_length=500)
    location_notes: str | None = Field(default=None, max_length=1000)

    @field_validator("address_line", "location_notes")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
