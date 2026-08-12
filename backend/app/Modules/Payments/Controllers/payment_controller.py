from app.Modules.Payments.Services.payment_service import PaymentService


class PaymentController:
    def __init__(self):
        self.service = PaymentService()

    def create_intent(self, user_id, data):
        return self.service.create_intent(user_id, data)

    def initiate(self, user_id, intent_id, payer_reference):
        return self.service.initiate(user_id, intent_id, payer_reference)

    def list_transactions(self, user_id, intent_id):
        return self.service.list_transactions(user_id, intent_id)


    def query_mpesa(self, user_id: int, intent_id: int):
        return self.service.query_mpesa(user_id, intent_id)
