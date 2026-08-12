from dataclasses import dataclass


@dataclass(frozen=True)
class Review:
    id: int
    public_id: str
    job_id: int
    reviewer_user_id: int
    reviewee_user_id: int
    direction: str
    status: str
    overall_rating: int
