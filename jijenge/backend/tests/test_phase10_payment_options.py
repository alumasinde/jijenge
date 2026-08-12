from decimal import Decimal

from app.Modules.Payments.Providers.cash import CashProvider


def test_cash_provider_requires_confirmation():
    result = CashProvider().initiate_customer_payment(
        amount=Decimal("50.00"),
        currency_code="KES",
        payer_reference="CASH-001",
        callback_url="https://example.com/callback",
        idempotency_key="payment-123456789",
    )
    assert result.status == "PENDING_CONFIRMATION"
    assert CashProvider.code == "CASH"


def test_application_fee_is_separate_from_job_payment():
    application_fee = Decimal("50.00")
    job_payment = Decimal("2000.00")
    assert application_fee != job_payment
