from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AvailabilityRuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day_of_week: int = Field(ge=1, le=7)
    start_time: time
    end_time: time
    effective_from: date | None = None
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        if (
            self.effective_from
            and self.effective_to
            and self.effective_to < self.effective_from
        ):
            raise ValueError("effective_to must not be before effective_from")
        return self


class AvailabilityExceptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exception_date: date
    is_available: bool = False
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_exception(self):
        if self.is_available:
            if not self.start_time or not self.end_time:
                raise ValueError(
                    "start_time and end_time are required when available"
                )
            if self.start_time >= self.end_time:
                raise ValueError("start_time must be before end_time")
        elif self.start_time or self.end_time:
            raise ValueError(
                "start_time and end_time must be omitted for unavailable exceptions"
            )
        return self


class MatchingPreferencesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_distance_km: float = Field(gt=0, le=500)
    accepts_new_jobs: bool = True
    auto_match_enabled: bool = True
    minimum_notice_minutes: int = Field(ge=0, le=10080)


class AvailabilityRuleResponse(AvailabilityRuleRequest):
    id: int
    is_active: bool


class AvailabilityExceptionResponse(AvailabilityExceptionRequest):
    id: int


class MatchingPreferencesResponse(MatchingPreferencesRequest):
    provider_id: int


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
