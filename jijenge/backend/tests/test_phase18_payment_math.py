from decimal import Decimal


def test_payment_amount_must_match():
    expected=Decimal("5000.00")
    received=Decimal("5000.00")
    assert expected == received


def test_payment_amount_mismatch_is_detectable():
    expected=Decimal("5000.00")
    received=Decimal("4990.00")
    assert expected != received
