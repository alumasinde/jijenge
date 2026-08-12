from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.Core.auth import AuthenticatedUser, require_role
from app.Modules.Financials.Controllers.payout_method_controller import PayoutMethodController

router=APIRouter(prefix="/payout-methods",tags=["Provider Payout Methods"])
controller=PayoutMethodController()


class CreatePayoutMethodRequest(BaseModel):
    method_type: str = Field(min_length=2,max_length=60)
    account_name: str = Field(min_length=2,max_length=160)
    account_reference: str = Field(min_length=3,max_length=255)


@router.post("")
def create(
    data: CreatePayoutMethodRequest,
    current_user: AuthenticatedUser=Depends(require_role("PROVIDER")),
):
    return controller.create(
        current_user.id,data.method_type,data.account_name,data.account_reference
    )


@router.get("")
def list_methods(
    current_user: AuthenticatedUser=Depends(require_role("PROVIDER")),
):
    return controller.list(current_user.id)
