from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

class JobTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notes: str | None = Field(default=None, max_length=2000)
    cancellation_reason: str | None = Field(default=None, max_length=1000)
    completion_notes: str | None = Field(default=None, max_length=2000)
    @field_validator("notes", "cancellation_reason", "completion_notes")
    @classmethod
    def clean_text(cls, value):
        if value is None: return None
        value = value.strip()
        return value or None

class JobLifecycleResponse(BaseModel):
    job_id: int
    status: str
    assigned_provider_id: int | None
    assigned_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    completion_notes: str | None

class JobEventResponse(BaseModel):
    id: int
    job_id: int
    event_type: str
    actor_user_id: int
    from_status: str | None
    to_status: str | None
    notes: str | None
    created_at: datetime
