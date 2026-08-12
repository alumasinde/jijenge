from app.Modules.Applications.Services.application_service import ApplicationService


class ApplicationController:
    def __init__(self):
        self.service = ApplicationService()

    def apply(self, user_id, job_id, data):
        return self.service.apply(user_id, job_id, data)

    def list_for_job(self, user_id, job_id):
        return self.service.list_for_job(user_id, job_id)

    def list_for_provider(self, user_id):
        return self.service.list_for_provider(user_id)

    def withdraw(self, user_id, application_id):
        return self.service.withdraw(user_id, application_id)

    def accept(self, user_id, application_id):
        return self.service.accept(user_id, application_id)

    def get_assignment_for_provider(self, user_id, assignment_id):
        return self.service.get_assignment_for_provider(user_id, assignment_id)

    def confirm_assignment(self, user_id, assignment_id):
        return self.service.confirm_assignment(user_id, assignment_id)

    def decline_assignment(self, user_id, assignment_id, reason):
        return self.service.decline_assignment(user_id, assignment_id, reason)
