from fastapi import APIRouter, Depends

from app.Core.auth import AuthenticatedUser, require_role
from app.Modules.Financials.Services.execution_service import FinancialExecutionService

router=APIRouter(prefix="/financial-executions",tags=["Financial Executions"])
service=FinancialExecutionService()


@router.post("/settlements/{settlement_id}/queue")
def queue_settlement(
    settlement_id:int,
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return {"execution_id":service.queue_settlement(settlement_id)}


@router.post("/{execution_id}/settlement")
def execute_settlement(
    execution_id:int,
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return service.execute_settlement(execution_id)


@router.post("/refunds/{refund_id}/queue")
def queue_refund(
    refund_id:int,
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return {"execution_id":service.queue_refund(refund_id)}


@router.post("/{execution_id}/refund")
def execute_refund(
    execution_id:int,
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return service.execute_refund(execution_id)
