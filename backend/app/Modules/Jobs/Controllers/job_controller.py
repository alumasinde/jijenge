from app.Modules.Jobs.Services.job_service import JobService


class JobController:
    def __init__(self):
        self.service = JobService()

    def create(self, customer_id: int, data):
        return self.service.create(customer_id, data)

    def get(self, customer_id: int, job_id: int):
        return self.service.get(customer_id, job_id)
