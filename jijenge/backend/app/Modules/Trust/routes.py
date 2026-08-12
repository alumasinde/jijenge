from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Trust.Controllers.trust_controller import TrustController
from app.Modules.Trust.schema import CreateTrustReportRequest

router = APIRouter(prefix="/trust", tags=["Trust & Safety"])
controller = TrustController()


@router.post("/reports", status_code=201)
def create_report(
    request: Request,
    data: CreateTrustReportRequest,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request,
        "trust:create-report",
        settings.auth_rate_limit_per_minute,
    )
    return controller.create_report(current_user.id, data)
