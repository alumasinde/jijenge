from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Verification.Controllers.verification_controller import (
    VerificationController,
)
from app.Modules.Verification.schema import (
    CreateVerificationRequest,
    VerificationDocumentInput,
    VerificationRequestResponse,
)

router = APIRouter(prefix="/verification", tags=["Verification"])
controller = VerificationController()


@router.post(
    "/requests",
    response_model=VerificationRequestResponse,
    status_code=201,
)
def create_request(
    request: Request,
    data: CreateVerificationRequest,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request,
        "verification:create",
        settings.auth_rate_limit_per_minute,
    )
    return controller.create_request(
        current_user.id,
        data.verification_type_code,
    )


@router.post("/requests/{request_id}/documents")
def add_document(
    request: Request,
    request_id: int,
    data: VerificationDocumentInput,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request,
        "verification:document",
        settings.auth_rate_limit_per_minute,
    )
    return controller.add_document(
        current_user.id,
        request_id,
        data,
    )


@router.get(
    "/requests",
    response_model=list[VerificationRequestResponse],
)
def list_requests(
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    return controller.list_requests(current_user.id)
