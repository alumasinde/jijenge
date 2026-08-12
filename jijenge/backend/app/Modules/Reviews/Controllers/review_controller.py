from app.Modules.Reviews.Services.review_service import ReviewService


class ReviewController:
    def __init__(self):
        self.service = ReviewService()

    def create(self, user_id, job_id, data):
        return self.service.create(user_id, job_id, data)

    def list_for_user(self, user_id, limit):
        return self.service.list_for_user(user_id, limit)

    def provider_summary(self, provider_user_id):
        return self.service.provider_summary(provider_user_id)
