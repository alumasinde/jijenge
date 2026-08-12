from app.Modules.Financials.Services.settlement_service import SettlementService


class SettlementController:
    def __init__(self):
        self.service = SettlementService()

    def request(self, user_id, earning_id, idempotency_key, payout_method_id=None):
        return self.service.request(
            user_id, earning_id, idempotency_key, payout_method_id
        )
