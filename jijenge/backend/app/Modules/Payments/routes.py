from fastapi import APIRouter, Depends, Query, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_active_user, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Payments.Controllers.cash_controller import CashController
from app.Modules.Payments.Controllers.payment_controller import PaymentController
from app.Modules.Payments.schema import (
    CreatePaymentIntentRequest,
    PaymentIntentResponse,
    PaymentTransactionResponse,
)

router = APIRouter(prefix="/payments", tags=["Payments"])
controller = PaymentController()
cash_controller = CashController()


@router.post("/intents", response_model=PaymentIntentResponse, status_code=201)
def create_payment_intent(
    request: Request,
    data: CreatePaymentIntentRequest,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request, "payments:create-intent",
        settings.auth_rate_limit_per_minute
    )
    return controller.create_intent(current_user.id, data)


@router.post("/intents/{intent_id}/initiate")
def initiate_payment(
    request: Request,
    intent_id: int,
    payer_reference: str | None = Query(default=None, max_length=120),
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request, "payments:initiate",
        settings.auth_rate_limit_per_minute
    )
    return controller.initiate(current_user.id, intent_id, payer_reference)


@router.get("/intents/{intent_id}/transactions", response_model=list[PaymentTransactionResponse])
def list_payment_transactions(
    intent_id: int,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    return controller.list_transactions(current_user.id, intent_id)


@router.post("/cash/{cash_record_id}/confirm")
def confirm_cash_payment(
    request: Request,
    cash_record_id: int,
    receipt_reference: str | None = Query(default=None, max_length=120),
    notes: str | None = Query(default=None, max_length=1000),
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    enforce_rate_limit(
        request, "payments:cash-confirm",
        settings.auth_rate_limit_per_minute
    )
    return cash_controller.confirm(
        cash_record_id=cash_record_id,
        recorder_user_id=current_user.id,
        receipt_reference=receipt_reference,
        notes=notes,
    )


@router.post("/webhooks/{provider_code}")
def payment_webhook(
    provider_code: str,
    payload: dict,
    request: Request,
):
    provider = controller.service.providers.get(provider_code)
    headers = {k: v for k, v in request.headers.items()}

    if not provider.verify_callback(payload, headers):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid payment callback")

    result = provider.parse_callback(payload)

    # Provider reference is used to locate the intent safely.
    if not result.provider_reference:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Callback has no provider reference")

    intent = controller.service.repository.find_intent_by_provider_reference(
        provider_code=provider_code.upper(),
        provider_reference=result.provider_reference,
    )
    if not intent:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Payment intent not found")

    return controller.service.process_callback(
        intent_id=int(intent["id"]),
        provider_code=provider_code.upper(),
        provider_event_id=result.provider_transaction_id,
        payload=payload,
        result_status=result.status,
        provider_transaction_id=result.provider_transaction_id,
        provider_reference=result.provider_reference,
        response_message=result.message,
        callback_amount=result.amount,
        callback_currency=result.currency_code,
    )


@router.post("/intents/{intent_id}/query")
def query_mpesa_payment(
    request: Request,
    intent_id: int,
    current_user: AuthenticatedUser = Depends(require_active_user),
):
    enforce_rate_limit(
        request, "payments:query",
        settings.auth_rate_limit_per_minute
    )
    return controller.query_mpesa(current_user.id, intent_id)
