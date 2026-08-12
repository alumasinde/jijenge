from fastapi import HTTPException

from app.Modules.Applications.Repositories.application_repository import ApplicationRepository
from app.Modules.Execution.Repositories.execution_repository import ExecutionRepository


class ExecutionService:
    def __init__(self):
        self.repository = ExecutionRepository()
        self.applications = ApplicationRepository()

    def _provider_id(self, user_id):
        row = self.applications.provider_profile_for_user(user_id)
        if not row:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        return int(row["id"])

    def _response(self, row):
        return row

    def provider_action(self, user_id, assignment_id, target, event, location, notes):
        provider_id = self._provider_id(user_id)
        try:
            return self.repository.transition_provider(
                assignment_id, provider_id, target, event, location, notes
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

    def complete(self, user_id, assignment_id, notes):
        provider_id = self._provider_id(user_id)
        try:
            return self.repository.submit_completion(
                assignment_id, provider_id, notes
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

    def confirm_completion(self, user_id, assignment_id):
        try:
            return self.repository.confirm_completion(assignment_id, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

    def dispute(self, user_id, assignment_id, data):
        try:
            dispute_id = self.repository.open_dispute(
                assignment_id, user_id, data.dispute_type, data.description
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return {"dispute_id": dispute_id}
