from pydantic import BaseModel, ConfigDict, Field


class ReviewDimensionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension_code: str = Field(min_length=2, max_length=60)
    score: int = Field(ge=1, le=5)


class CreateReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=180)
    body: str | None = Field(default=None, max_length=3000)
    dimension_scores: list[ReviewDimensionInput] = Field(
        default_factory=list,
        max_length=10,
    )


class ReviewResponse(BaseModel):
    public_id: str
    job_id: int
    reviewer_user_id: int
    reviewee_user_id: int
    direction: str
    status: str
    overall_rating: int
    title: str | None
    body: str | None
    created_at: str


class ProviderRatingResponse(BaseModel):
    provider_user_id: int
    published_review_count: int
    overall_rating_average: float | None
    quality_average: float | None
    communication_average: float | None
    punctuality_average: float | None
    professionalism_average: float | None
