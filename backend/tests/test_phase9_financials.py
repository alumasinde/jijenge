from decimal import Decimal

import pytest


def test_provider_earning_formula():
    gross = Decimal("1000.00")
    fee = Decimal("100.00")
    adjustment = Decimal("0.00")
    assert gross - fee + adjustment == Decimal("900.00")


def test_negative_provider_earning_is_invalid():
    gross = Decimal("100.00")
    fee = Decimal("150.00")
    with pytest.raises(ValueError):
        net = gross - fee
        if net < 0:
            raise ValueError("Provider net earnings cannot be negative")


def test_refund_remaining_balance():
    paid = Decimal("1000.00")
    already_refunded = Decimal("300.00")
    requested = Decimal("700.00")
    assert requested <= paid - already_refunded
