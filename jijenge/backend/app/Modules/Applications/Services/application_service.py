from fastapi import HTTPException, status

from app.Modules.Applications.Repositories.application_repository import ApplicationRepository
from app.Modules.Applications.schema import (
    ApplicationListResponse,
    ApplicationResponse,
    AssignmentResponse,
    CreateApplicationRequest,
)


class ApplicationService:
    def __init__(self):
        self.repository = ApplicationRepository()

    def _response(self, row):
        return ApplicationResponse(
            id=int(row["id"]),
            job_id=int(row["job_id"]),
            provider_id=int(row["provider_id"]),
            status=row["status_code"],
            proposed_price=row["proposed_price"],
            message=row["message"],
            estimated_start_at=row["estimated_start_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            responded_at=row["responded_at"],
        )

    def _provider_id(self, user_id: int) -> int:
        row = self.repository.provider_profile_for_user(user_id)
        if not row:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        if self.repository.get_provider_status_code(int(row["id"])) != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Provider is not active",
            )
        return int(row["id"])

    def apply(self, user_id: int, job_id: int, data: CreateApplicationRequest):
        provider_id = self._provider_id(user_id)
        job = self.repository.get_job_for_application(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job["status_code"] != "OPEN":
            raise HTTPException(status_code=409, detail="Job is no longer accepting applications")
        if not self.repository.provider_offers_service(provider_id, int(job["service_id"])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Provider does not offer the requested service",
            )

        if not self.repository.provider_can_reach_job(provider_id, job_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Job location is outside the provider's configured service area",
            )

        try:
            row = self.repository.create_application(
                job_id, provider_id, data.proposed_price,
                data.message, data.estimated_start_at
            )
        except Exception as exc:
            if "Duplicate entry" in str(exc):
                raise HTTPException(
                    status_code=409,
                    detail="You have already applied to this job",
                )
            raise

        return self._response(row)

    def list_for_job(self, customer_id: int, job_id: int):
        job = self.repository.get_job_for_application(job_id)
        if not job or int(job["customer_id"]) != customer_id:
            raise HTTPException(status_code=404, detail="Job not found")
        rows = self.repository.list_for_job(job_id)
        return ApplicationListResponse(
            items=[self._response(r) for r in rows],
            total=len(rows),
        )

    def list_for_provider(self, user_id: int):
        provider_id = self._provider_id(user_id)
        rows = self.repository.list_for_provider(provider_id)
        return ApplicationListResponse(
            items=[self._response(r) for r in rows],
            total=len(rows),
        )

    def withdraw(self, user_id: int, application_id: int):
        provider_id = self._provider_id(user_id)
        row = self.repository.get_application_for_provider(application_id, provider_id)
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        if row["status_code"] != "PENDING":
            raise HTTPException(status_code=409, detail="Only pending applications can be withdrawn")
        row = self.repository.withdraw(application_id, provider_id)
        return self._response(row)

    def accept(self, customer_id: int, application_id: int):
        try:
            row = self.repository.accept_and_assign(application_id, customer_id)
        except PermissionError:
            raise HTTPException(status_code=404, detail="Application not found")
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return self._assignment_response(row)

    def get_assignment_for_provider(self, user_id: int, assignment_id: int):
        provider_id = self._provider_id(user_id)
        row = self.repository.get_assignment_for_provider(
            assignment_id, provider_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return self._assignment_response(row)

    def confirm_assignment(self, user_id: int, assignment_id: int):
        provider_id = self._provider_id(user_id)
        try:
            row = self.repository.confirm_assignment(
                assignment_id, provider_id
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return self._assignment_response(row)

    def decline_assignment(self, user_id: int, assignment_id: int, reason):
        provider_id = self._provider_id(user_id)
        try:
            row = self.repository.decline_assignment(
                assignment_id, provider_id, reason
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return self._assignment_response(row)

    def _assignment_response(self, row):
        return AssignmentResponse(
            id=int(row["id"]),
            job_id=int(row["job_id"]),
            provider_id=int(row["provider_id"]),
            application_id=(
                int(row["application_id"])
                if row["application_id"] is not None else None
            ),
            status=row["status_code"],
            assigned_by_user_id=int(row["assigned_by_user_id"]),
            assigned_at=row["assigned_at"],
            confirmation_deadline=row["confirmation_deadline"],
            confirmed_at=row["confirmed_at"],
            declined_at=row["declined_at"],
            decline_reason=row["decline_reason"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            cancelled_at=row["cancelled_at"],
        )
