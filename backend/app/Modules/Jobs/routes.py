from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Jobs.Controllers.job_controller import JobController
from app.Modules.Jobs.schema import CreateJobRequest, JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])
controller = JobController()


@router.post("", response_model=JobResponse, status_code=201)
def create_job(
    request: Request,
    data: CreateJobRequest,
    current_user: AuthenticatedUser = Depends(require_role("CUSTOMER")),
):
    enforce_rate_limit(
        request, "jobs:create", settings.auth_rate_limit_per_minute
    )
    return controller.create(current_user.id, data)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    current_user: AuthenticatedUser = Depends(require_role("CUSTOMER")),
):
    return controller.get(current_user.id, job_id)
