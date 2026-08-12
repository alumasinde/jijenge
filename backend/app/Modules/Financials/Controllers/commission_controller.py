from app.Modules.Financials.Services.commission_service import CommissionService


class CommissionController:
    def __init__(self):
        self.service = CommissionService()

    def finalize(self, assignment_id, processing_fee=0):
        return self.service.finalize_job_financials(
            assignment_id, processing_fee
        )
