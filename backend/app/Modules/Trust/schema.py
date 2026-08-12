from pydantic import BaseModel, ConfigDict, Field


class CreateTrustReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_type_code: str = Field(min_length=2, max_length=60)
    reported_user_id: int | None = Field(default=None, ge=1)
    job_id: int | None = Field(default=None, ge=1)
    review_id: int | None = Field(default=None, ge=1)
    description: str = Field(min_length=10, max_length=3000)
    evidence: list[str] = Field(default_factory=list, max_length=10)
