from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_role, require_active_user
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Disputes.Services.dispute_service import DisputeService
from app.Modules.Disputes.Services.refund_service import RefundService
from app.Modules.Disputes.schema import (
    OpenDisputeRequest,ResolveDisputeRequest,CreateRefundRequest
)

router=APIRouter(prefix="/disputes",tags=["Disputes"])
disputes=DisputeService()
refunds=RefundService()


@router.post("/assignments/{assignment_id}")
def open_dispute(
    request:Request,assignment_id:int,data:OpenDisputeRequest,
    current_user:AuthenticatedUser=Depends(require_active_user),
):
    enforce_rate_limit(request,"disputes:open",settings.auth_rate_limit_per_minute)
    return disputes.open(
        current_user.id,assignment_id,data.reason,data.description,data.disputed_amount
    )


@router.get("/{dispute_id}")
def get_dispute(
    dispute_id:int,
    current_user:AuthenticatedUser=Depends(require_active_user),
):
    return disputes.get(current_user.id,dispute_id)


@router.post("/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id:int,data:ResolveDisputeRequest,
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return disputes.resolve(
        current_user.id,dispute_id,data.status,data.resolved_amount,data.notes
    )


@router.post("/payments/{payment_id}/refunds")
def request_refund(
    request:Request,payment_id:int,data:CreateRefundRequest,
    current_user:AuthenticatedUser=Depends(require_role("CUSTOMER")),
):
    enforce_rate_limit(request,"refunds:request",settings.auth_rate_limit_per_minute)
    return refunds.request(
        current_user.id,payment_id,data.amount,data.reason,
        data.idempotency_key,data.dispute_id
    )


@router.get("/refunds/{refund_id}")
def get_refund(
    refund_id:int,
    current_user:AuthenticatedUser=Depends(require_role("CUSTOMER")),
):
    return refunds.get(current_user.id,refund_id)


@router.post("/refunds/{refund_id}/approve")
def approve_refund(
    refund_id:int,data:dict,
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return refunds.approve(
        current_user.id,refund_id,
        data.get("approved_amount"),
        data.get("notes"),
    )
