from fastapi import APIRouter, Depends, Query

from app.Core.auth import AuthenticatedUser, require_role, require_active_user
from app.Modules.Financials.Services.report_service import FinancialReportService

router=APIRouter(prefix="/financial-reports",tags=["Financial Reports"])
service=FinancialReportService()


@router.get("/summary")
def summary(
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return service.summary()


@router.get("/kpis")
def kpis(
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return service.kpis()


@router.get("/payments")
def payment_history(
    limit:int=Query(default=50,ge=1,le=100),
    offset:int=Query(default=0,ge=0),
    current_user:AuthenticatedUser=Depends(require_active_user),
):
    return service.payment_history(current_user.id,limit,offset)


@router.get("/provider-statement")
def provider_statement(
    limit:int=Query(default=100,ge=1,le=200),
    offset:int=Query(default=0,ge=0),
    current_user:AuthenticatedUser=Depends(require_role("PROVIDER")),
):
    return service.provider_statement(current_user.id,limit,offset)


@router.get("/exceptions")
def exceptions(
    limit:int=Query(default=100,ge=1,le=200),
    offset:int=Query(default=0,ge=0),
    current_user:AuthenticatedUser=Depends(require_role("ADMIN")),
):
    return service.exceptions(limit,offset)
