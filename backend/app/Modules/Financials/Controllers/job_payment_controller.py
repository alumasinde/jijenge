from app.Modules.Financials.Services.job_payment_service import JobPaymentService


class JobPaymentController:
    def __init__(self):
        self.service=JobPaymentService()

    def create(self,user_id,assignment_id,data):
        return self.service.create(
            assignment_id,user_id,data.payment_method,data.idempotency_key
        )

    def create_intent(self,user_id,payment_id):
        return self.service.create_intent(payment_id,user_id)

    def get(self,user_id,payment_id):
        return self.service.get(payment_id,user_id)
