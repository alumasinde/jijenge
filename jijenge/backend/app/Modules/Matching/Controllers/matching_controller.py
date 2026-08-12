from app.Modules.Matching.Services.matching_service import MatchingService


class MatchingController:
    def __init__(self):
        self.service = MatchingService()

    def match_job(self, customer_id, job_id, limit, refresh):
        return self.service.match_job(customer_id, job_id, limit, refresh)

    def dispatch_job(self, job_id):
        return self.service.dispatch_job(job_id)

    def view(self, provider_user_id, job_id):
        return self.service.view(provider_user_id, job_id)

    def respond(self, provider_user_id, job_id, data):
        return self.service.respond(provider_user_id, job_id, data)
