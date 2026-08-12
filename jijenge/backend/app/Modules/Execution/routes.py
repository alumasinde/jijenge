from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Execution.Controllers.execution_controller import ExecutionController
from app.Modules.Execution.schema import (
    CompletionRequest,
    DisputeRequest,
    ExecutionActionRequest,
    ExecutionResponse,
)

router = APIRouter(prefix="/execution", tags=["Job Execution"])
controller = ExecutionController()


@router.get("/assignments/{assignment_id}", response_model=ExecutionResponse)
def get_execution(
    assignment_id: int,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    provider_id = controller.service._provider_id(current_user.id)
    row = controller.service.repository.get_for_provider(assignment_id, provider_id)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Assignment not found")
    return row


def action(target, event):
    def endpoint(
        request: Request,
        assignment_id: int,
        data: ExecutionActionRequest,
        current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
    ):
        enforce_rate_limit(
            request, f"execution:{target.lower()}",
            settings.auth_rate_limit_per_minute
        )
        return controller.provider_action(
            current_user.id, assignment_id, target, event,
            data.location, data.notes
        )
    return endpoint


router.post(
    "/assignments/{assignment_id}/on-the-way",
    response_model=ExecutionResponse,
)(action("ON_THE_WAY", "ON_THE_WAY"))

router.post(
    "/assignments/{assignment_id}/arrived",
    response_model=ExecutionResponse,
)(action("ARRIVED", "ARRIVED"))

router.post(
    "/assignments/{assignment_id}/start",
    response_model=ExecutionResponse,
)(action("IN_PROGRESS", "STARTED"))

router.post(
    "/assignments/{assignment_id}/pause",
    response_model=ExecutionResponse,
)(action("PAUSED", "PAUSED"))

router.post(
    "/assignments/{assignment_id}/resume",
    response_model=ExecutionResponse,
)(action("IN_PROGRESS", "RESUMED"))

router.post(
    "/assignments/{assignment_id}/complete",
    response_model=ExecutionResponse,
)
def complete(
    request: Request,
    assignment_id: int,
    data: CompletionRequest,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "execution:complete",
        settings.auth_rate_limit_per_minute
    )
    return controller.complete(current_user.id, assignment_id, data.notes)


router.post(
    "/assignments/{assignment_id}/confirm-completion",
    response_model=ExecutionResponse,
)
def confirm_completion(
    request: Request,
    assignment_id: int,
    current_user: AuthenticatedUser = Depends(require_role("CUSTOMER")),
):
    enforce_rate_limit(
        request, "execution:confirm-completion",
        settings.auth_rate_limit_per_minute
    )
    return controller.confirm_completion(current_user.id, assignment_id)


@router.post("/assignments/{assignment_id}/disputes")
def dispute(
    request: Request,
    assignment_id: int,
    data: DisputeRequest,
    current_user: AuthenticatedUser = Depends(require_role("CUSTOMER")),
):
    enforce_rate_limit(
        request, "execution:dispute",
        settings.auth_rate_limit_per_minute
    )
    return controller.dispute(current_user.id, assignment_id, data)
