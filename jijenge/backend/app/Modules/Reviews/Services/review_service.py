from fastapi import HTTPException

from app.Modules.Reviews.Repositories.review_repository import ReviewRepository


class ReviewService:
    def __init__(self):
        self.repository = ReviewRepository()

    def create(self, reviewer_user_id: int, job_id: int, data):
        context = self.repository.get_review_context(
            job_id, reviewer_user_id
        )

        if not context:
            raise HTTPException(
                status_code=403,
                detail="You are not a participant in this job",
            )

        if context["job_status"] != "COMPLETED":
            raise HTTPException(
                status_code=409,
                detail="Reviews can only be submitted after job completion",
            )

        if not context["reviewee_user_id"]:
            raise HTTPException(
                status_code=409,
                detail="This job does not have a valid reviewee",
            )

        dimension_scores = {}
        for item in data.dimension_scores:
            code = item.dimension_code.strip().upper()
            if code in dimension_scores:
                raise HTTPException(
                    status_code=422,
                    detail=f"Duplicate rating dimension: {code}",
                )
            dimension_scores[code] = item.score

        try:
            return self.repository.create(
                job_id=job_id,
                reviewer_user_id=reviewer_user_id,
                reviewee_user_id=context["reviewee_user_id"],
                direction_code=context["direction_code"],
                overall_rating=data.overall_rating,
                title=data.title.strip() if data.title else None,
                body=data.body.strip() if data.body else None,
                dimension_scores=dimension_scores,
            )
        except ValueError as exc:
            message = str(exc)
            if "Duplicate entry" in message:
                raise HTTPException(
                    status_code=409,
                    detail="You have already reviewed this participant for this job",
                )
            raise HTTPException(status_code=422, detail=message)

    def list_for_user(self, user_id: int, limit: int = 20):
        return self.repository.list_for_user(user_id, limit)

    def provider_summary(self, provider_user_id: int):
        row = self.repository.provider_summary(provider_user_id)
        if not row:
            return {
                "provider_user_id": provider_user_id,
                "published_review_count": 0,
                "overall_rating_average": None,
                "quality_average": None,
                "communication_average": None,
                "punctuality_average": None,
                "professionalism_average": None,
            }
        return row
