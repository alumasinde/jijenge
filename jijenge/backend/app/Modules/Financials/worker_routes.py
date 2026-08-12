from fastapi import APIRouter, Depends

from app.Core.auth import AuthenticatedUser, require_role
from app.Modules.Financials.Services.reconciliation_worker import ReconciliationWorker
from app.Modules.Financials.Services.retry_worker import RetryWorker

router=APIRouter(prefix="/financial-workers",tags=["Financial Workers"])
reconciliation=ReconciliationWorker()
retry=RetryWorker()


@router.post("/reconcile")
def reconcile(
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return reconciliation.run()


@router.post("/retry")
def retry_failed(
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return retry.run()
