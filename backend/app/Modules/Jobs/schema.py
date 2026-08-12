from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.Modules.Locations.schema import JobLocationRequest


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_id: int = Field(ge=1)
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=10000)
    location: JobLocationRequest
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    preferred_start_at: datetime | None = None
    preferred_end_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = " ".join(value.strip().split())
        if not value:
            raise ValueError("Title is required")
        return value

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Description is required")
        return value


class JobResponse(BaseModel):
    id: int
    customer_id: int
    service_id: int
    service_code: str
    service_name: str
    status: str
    title: str
    description: str
    budget_min: Decimal | None
    budget_max: Decimal | None
    preferred_start_at: datetime | None
    preferred_end_at: datetime | None
    latitude: float
    longitude: float
    address_line: str | None
    location_notes: str | None
    created_at: datetime
    updated_at: datetime


class JobAssignmentResponse(BaseModel):
    id: int
    job_id: int
    provider_id: int
    application_id: int | None
    assigned_at: datetime
