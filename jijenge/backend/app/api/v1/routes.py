
from fastapi import APIRouter
from app.api.v1.system_routes import router as system_router

from app.Modules.Availability.routes import router as availability_router
from app.Modules.Matching.routes import router as matching_router
from app.Modules.Execution.routes import router as execution_router
from app.Modules.Financials.commission_routes import router as commission_router
from app.Modules.Financials.job_payment_routes import router as job_payment_router
from app.Modules.Financials.settlement_routes import router as settlement_router
from app.Modules.Financials.payout_method_routes import router as payout_method_router
from app.Modules.Applications.routes import router as applications_router
from app.Modules.Auth.routes import router as auth_router
from app.Modules.Financials.routes import router as financials_router
from app.Modules.Jobs.routes import router as jobs_router
from app.Modules.Locations.routes import router as locations_router
from app.Modules.Notifications.routes import router as notifications_router
from app.Modules.Payments.routes import router as payments_router
from app.Modules.Providers.routes import router as providers_router
from app.Modules.Reviews.routes import router as reviews_router
from app.Modules.Services.routes import router as services_router
from app.Modules.Trust.routes import router as trust_router
from app.Modules.Users.routes import router as users_router
from app.Modules.Verification.routes import router as verification_router
from app.Modules.Disputes.routes import router as disputes_router
from app.Modules.Financials.execution_routes import router as execution_router
from app.Modules.Financials.worker_routes import router as worker_router
from app.Modules.Financials.report_routes import router as financial_report_router

router = APIRouter()
router.include_router(system_router)

for module_router in (
    auth_router, users_router, services_router, providers_router,
    locations_router, jobs_router, applications_router, availability_router,
    matching_router, notifications_router, payments_router, financials_router,
    reviews_router, verification_router, trust_router, execution_router,
    commission_router, job_payment_router, settlement_router,
    payout_method_router, disputes_router, worker_router, financial_report_router,
):
    router.include_router(module_router)
