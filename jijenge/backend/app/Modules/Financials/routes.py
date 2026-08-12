from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Financials.Controllers.financial_controller import FinancialController

router = APIRouter(prefix="/financials", tags=["Financials"])
controller = FinancialController()


@router.post("/refunds")
def request_refund(
    request: Request,
    payment_intent_id: int,
    amount: Decimal,
    idempotency_key: str = Query(min_length=16, max_length=160),
    reason: str | None = Query(default=None, max_length=1000),
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request, "financials:refund", settings.auth_rate_limit_per_minute
    )
    return controller.request_refund(
        requester_user_id=current_user.id,
        payment_intent_id=payment_intent_id,
        amount=amount,
        reason=reason,
        idempotency_key=idempotency_key,
    )


@router.post("/settlements")
def request_settlement(
    request: Request,
    amount: Decimal,
    destination_type: str = Query(min_length=2, max_length=50),
    destination_reference: str = Query(min_length=3, max_length=255),
    idempotency_key: str = Query(min_length=16, max_length=160),
    current_user: AuthenticatedUser = Depends(require_role("PROVIDER")),
):
    enforce_rate_limit(
        request, "financials:settlement", settings.auth_rate_limit_per_minute
    )
    return controller.request_settlement(
        provider_user_id=current_user.id,
        amount=amount,
        destination_type=destination_type,
        destination_reference=destination_reference,
        idempotency_key=idempotency_key,
    )
