from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ProviderPaymentResult:
    status: str
    provider_transaction_id: str | None
    provider_reference: str | None
    amount: Decimal | None
    currency_code: str | None
    message: str | None = None


@dataclass(frozen=True)
class ProviderRequestResult:
    status: str
    provider_request_id: str | None
    provider_reference: str | None
    response: dict[str, Any] | None = None
    message: str | None = None


class PaymentProvider:
    code: str

    def initiate_customer_payment(
        self, *, amount: Decimal, currency_code: str,
        payer_reference: str, callback_url: str,
        idempotency_key: str
    ) -> ProviderRequestResult:
        raise NotImplementedError

    def request_payout(
        self, *, amount: Decimal, currency_code: str,
        payout_reference: str, destination_reference: str,
        idempotency_key: str
    ) -> ProviderRequestResult:
        raise NotImplementedError

    def request_refund(
        self, *, amount: Decimal, currency_code: str,
        provider_transaction_id: str, idempotency_key: str
    ) -> ProviderRequestResult:
        raise NotImplementedError

    def verify_callback(self, payload: dict, headers: dict[str, str]) -> bool:
        raise NotImplementedError

    def parse_callback(self, payload: dict) -> ProviderPaymentResult:
        raise NotImplementedError
