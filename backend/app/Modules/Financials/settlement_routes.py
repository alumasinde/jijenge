from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Financials.Controllers.settlement_controller import SettlementController
from app.Modules.Financials.Services.settlement_service import SettlementService

router = APIRouter(prefix="/settlements", tags=["Provider Settlements"])
controller = SettlementController()
service = SettlementService()


@router.post("/earnings/{earning_id}")
def request_settlement(
    request: Request,
    earning_id: int,
    idempotency_key: str,
    payout_method_id: int | None = None,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "settlements:request",
        settings.auth_rate_limit_per_minute
    )
    return controller.request(
        current_user.id, earning_id, idempotency_key, payout_method_id
    )


@router.get("/{settlement_id}")
def get_settlement(
    settlement_id: int,
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    return service.get(current_user.id, settlement_id)
