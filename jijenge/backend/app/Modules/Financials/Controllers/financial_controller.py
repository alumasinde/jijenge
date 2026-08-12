from app.Modules.Financials.Services.refund_service import RefundService
from app.Modules.Financials.Services.settlement_service import SettlementService


class FinancialController:
    def __init__(self):
        self.refunds = RefundService()
        self.settlements = SettlementService()

    def request_refund(self, **kwargs):
        return self.refunds.request(**kwargs)

    def request_settlement(self, **kwargs):
        return self.settlements.request(**kwargs)
