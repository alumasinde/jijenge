import pytest
from pydantic import ValidationError

from app.Modules.Payments.schema import CreatePaymentIntentRequest


def test_payment_amount_must_be_positive():
    with pytest.raises(ValidationError):
        CreatePaymentIntentRequest(
            payment_method="MPESA",
            amount=0,
            idempotency_key="payment-key-123456",
        )


def test_currency_is_normalized():
    data = CreatePaymentIntentRequest(
        payment_method="MPESA",
        amount="250.00",
        currency_code="kes",
        idempotency_key="payment-key-123456",
    )
    assert data.currency_code == "KES"


def test_idempotency_key_is_required():
    with pytest.raises(ValidationError):
        CreatePaymentIntentRequest(
            payment_method="MPESA",
            amount="250.00",
            idempotency_key="short",
        )
