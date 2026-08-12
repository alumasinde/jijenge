
from app.Modules.Payments.Providers.base import PaymentProvider, ProviderRequestResult


class CashProvider(PaymentProvider):
    code = "CASH"

    def initiate_customer_payment(self, **kwargs):
        return ProviderRequestResult(
            status="PENDING_CONFIRMATION",
            provider_request_id=None,
            provider_reference=None,
            response=None,
            message="Cash payment awaits authorized confirmation",
        )

    def request_payout(self, **kwargs):
        raise RuntimeError("Cash payout requires an authorized operational workflow")

    def request_refund(self, **kwargs):
        raise RuntimeError("Cash refund requires an authorized operational workflow")

    def verify_callback(self, payload, headers):
        return False

    def parse_callback(self, payload):
        raise NotImplementedError
