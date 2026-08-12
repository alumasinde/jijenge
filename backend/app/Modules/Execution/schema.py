from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExecutionLocation(BaseModel):
    latitude: Decimal = Field(ge=-90, le=90)
    longitude: Decimal = Field(ge=-180, le=180)


class ExecutionActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location: ExecutionLocation | None = None
    notes: str | None = Field(default=None, max_length=2000)


class CompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notes: str | None = Field(default=None, max_length=4000)


class DisputeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dispute_type: str = Field(min_length=1, max_length=60)
    description: str = Field(min_length=1, max_length=4000)


class ExecutionResponse(BaseModel):
    assignment_id: int
    job_id: int
    status: str
    assigned_at: datetime
    confirmed_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    customer_confirmation_deadline: datetime | None
