from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Applications.Controllers.application_controller import ApplicationController
from app.Modules.Applications.schema import (
    ApplicationListResponse,
    ApplicationResponse,
    AssignmentResponse,
    CreateApplicationRequest,
    AssignmentDecisionRequest,
)

router = APIRouter(prefix="/applications", tags=["Job Applications"])
controller = ApplicationController()


@router.post(
    "/jobs/{job_id}",
    response_model=ApplicationResponse,
    status_code=201,
)
def apply_to_job(
    request: Request,
    job_id: int,
    data: CreateApplicationRequest,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "applications:create", settings.auth_rate_limit_per_minute
    )
    return controller.apply(current_user.id, job_id, data)


@router.get(
    "/jobs/{job_id}",
    response_model=ApplicationListResponse,
)
def list_job_applications(
    job_id: int,
    current_user: AuthenticatedUser = Depends(require_role("CUSTOMER")),
):
    return controller.list_for_job(current_user.id, job_id)


@router.get(
    "/me",
    response_model=ApplicationListResponse,
)
def my_applications(
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    return controller.list_for_provider(current_user.id)


@router.post(
    "/{application_id}/withdraw",
    response_model=ApplicationResponse,
)
def withdraw_application(
    request: Request,
    application_id: int,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "applications:withdraw", settings.auth_rate_limit_per_minute
    )
    return controller.withdraw(current_user.id, application_id)


@router.post(
    "/{application_id}/accept",
    response_model=AssignmentResponse,
)
def accept_application(
    request: Request,
    application_id: int,
    current_user: AuthenticatedUser = Depends(require_role("CUSTOMER")),
):
    enforce_rate_limit(
        request, "applications:accept", settings.auth_rate_limit_per_minute
    )
    return controller.accept(current_user.id, application_id)


@router.get(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
)
def get_assignment(
    assignment_id: int,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    return controller.get_assignment_for_provider(
        current_user.id, assignment_id
    )


@router.post(
    "/assignments/{assignment_id}/confirm",
    response_model=AssignmentResponse,
)
def confirm_assignment(
    request: Request,
    assignment_id: int,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "assignments:confirm", settings.auth_rate_limit_per_minute
    )
    return controller.confirm_assignment(current_user.id, assignment_id)


@router.post(
    "/assignments/{assignment_id}/decline",
    response_model=AssignmentResponse,
)
def decline_assignment(
    request: Request,
    assignment_id: int,
    data: AssignmentDecisionRequest,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "assignments:decline", settings.auth_rate_limit_per_minute
    )
    return controller.decline_assignment(
        current_user.id, assignment_id, data.reason
    )
