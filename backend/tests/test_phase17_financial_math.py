from decimal import Decimal


def test_provider_net_math():
    gross = Decimal("5000.00")
    commission = Decimal("500.00")
    processing = Decimal("80.00")
    assert gross - commission - processing == Decimal("4420.00")


def test_platform_revenue():
    gross = Decimal("5000.00")
    rate = Decimal("10")
    assert gross * rate / Decimal("100") == Decimal("500.00")
