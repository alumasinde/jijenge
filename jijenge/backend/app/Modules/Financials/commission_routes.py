from decimal import Decimal

from fastapi import APIRouter, Depends

from app.Core.auth import AuthenticatedUser, require_role
from app.Modules.Financials.Controllers.commission_controller import CommissionController

router = APIRouter(prefix="/financials", tags=["Financials"])
controller = CommissionController()


@router.post("/assignments/{assignment_id}/finalize")
def finalize_assignment_financials(
    assignment_id: int,
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    # This endpoint is deliberately admin-protected for now.
    # Automatic payment/settlement orchestration can call the same service later.
    return controller.finalize(assignment_id, Decimal("0.00"))
