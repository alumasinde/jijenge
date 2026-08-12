from app.Modules.Payments.Providers.cash import CashProvider
from app.Modules.Payments.Providers.mpesa import MpesaProvider


class PaymentProviderRegistry:
    def __init__(self, config):
        self.providers = {
            "CASH": CashProvider(),
            "MPESA": MpesaProvider(config),
        }

    def get(self, provider_code):
        code=provider_code.upper()
        provider=self.providers.get(code)
        if not provider:
            raise ValueError(f"Unsupported payment provider: {code}")
        return provider
