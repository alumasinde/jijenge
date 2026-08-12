from pydantic import BaseModel, ConfigDict, Field


class MatchCandidateResponse(BaseModel):
    provider_id: int
    business_name: str | None
    professional_title: str | None
    distance_km: float
    within_service_area: bool
    available_for_job: bool
    verified: bool
    rating_average: float | None
    experience_years: float | None
    match_score: float


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = Field(default=20, ge=1, le=100)
    refresh: bool = False


class MatchResponseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accepted: bool
    reason: str | None = Field(default=None, max_length=500)


class MatchLifecycleResponse(BaseModel):
    job_id: int
    provider_id: int
    status: str
    notified_at: object | None
    viewed_at: object | None
    responded_at: object | None
    decline_reason: str | None
