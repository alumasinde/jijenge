from app.Modules.Execution.Services.execution_service import ExecutionService


class ExecutionController:
    def __init__(self):
        self.service = ExecutionService()

    def provider_action(self, user_id, assignment_id, target, event, location, notes):
        return self.service.provider_action(
            user_id, assignment_id, target, event, location, notes
        )

    def complete(self, user_id, assignment_id, notes):
        return self.service.complete(user_id, assignment_id, notes)

    def confirm_completion(self, user_id, assignment_id):
        return self.service.confirm_completion(user_id, assignment_id)

    def dispute(self, user_id, assignment_id, data):
        return self.service.dispute(user_id, assignment_id, data)
