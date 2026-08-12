from fastapi import HTTPException, status

from app.Modules.Jobs.Repositories.job_repository import JobRepository
from app.Modules.Jobs.schema import CreateJobRequest, JobResponse


class JobService:
    def __init__(self):
        self.repository = JobRepository()

    def create(self, customer_id: int, data: CreateJobRequest) -> JobResponse:
        if not self.repository.service_exists(data.service_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found",
            )

        if (
            data.preferred_start_at
            and data.preferred_end_at
            and data.preferred_end_at < data.preferred_start_at
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="preferred_end_at must be after preferred_start_at",
            )

        row = self.repository.create(
            customer_id=customer_id,
            service_id=data.service_id,
            title=data.title,
            description=data.description,
            latitude=data.location.latitude,
            longitude=data.location.longitude,
            address_line=data.location.address_line,
            location_notes=data.location.location_notes,
            budget_min=data.budget_min,
            budget_max=data.budget_max,
            preferred_start_at=data.preferred_start_at,
            preferred_end_at=data.preferred_end_at,
        )

        return self._response(row)

    def get(self, customer_id: int, job_id: int) -> JobResponse:
        row = self.repository.get_by_id(job_id, customer_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )
        return self._response(row)

    def _response(self, row: dict) -> JobResponse:
        return JobResponse(
            id=int(row["id"]),
            customer_id=int(row["customer_id"]),
            service_id=int(row["service_id"]),
            service_code=row["service_code"],
            service_name=row["service_name"],
            status=row["status_code"],
            title=row["title"],
            description=row["description"],
            budget_min=row["budget_min"],
            budget_max=row["budget_max"],
            preferred_start_at=row["preferred_start_at"],
            preferred_end_at=row["preferred_end_at"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            address_line=row["address_line"],
            location_notes=row["location_notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
