from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.Core.auth import AuthenticatedUser, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.Financials.Controllers.job_payment_controller import JobPaymentController
from app.Modules.Financials.schema import CreateJobPaymentRequest, JobPaymentResponse

router=APIRouter(prefix="/payments",tags=["Job Payments"])
controller=JobPaymentController()


@router.post(
    "/assignments/{assignment_id}",
    response_model=JobPaymentResponse,
    status_code=201,
)
def create_job_payment(
    request:Request,
    assignment_id:int,
    data:CreateJobPaymentRequest,
    current_user:AuthenticatedUser=Depends(require_role("CUSTOMER")),
):
    enforce_rate_limit(request,"payments:create",settings.auth_rate_limit_per_minute)
    return controller.create(current_user.id,assignment_id,data)


@router.post("/job-payments/{payment_id}/payment-intent")
def create_job_payment_intent(
    request:Request,
    payment_id:int,
    current_user:AuthenticatedUser=Depends(require_role("CUSTOMER")),
):
    enforce_rate_limit(request,"payments:intent",settings.auth_rate_limit_per_minute)
    return controller.create_intent(current_user.id,payment_id)


@router.get("/job-payments/{payment_id}",response_model=JobPaymentResponse)
def get_job_payment(
    payment_id:int,
    current_user:AuthenticatedUser=Depends(require_role("CUSTOMER")),
):
    return controller.get(current_user.id,payment_id)
