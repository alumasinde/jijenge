from decimal import Decimal

from app.Modules.Financials.Services.commission_service import CommissionService


def test_percentage_commission():
    service = CommissionService()
    rule = {
        "rule_type": "PERCENTAGE",
        "percentage_rate": Decimal("10.0000"),
        "fixed_amount": None,
        "min_fee": None,
        "max_fee": None,
    }
    assert service.calculate(Decimal("5000.00"), rule) == Decimal("500.00")


def test_fixed_commission():
    service = CommissionService()
    rule = {
        "rule_type": "FIXED",
        "percentage_rate": None,
        "fixed_amount": Decimal("150.00"),
        "min_fee": None,
        "max_fee": None,
    }
    assert service.calculate(Decimal("5000.00"), rule) == Decimal("150.00")


def test_min_max_commission():
    service = CommissionService()
    rule = {
        "rule_type": "PERCENTAGE",
        "percentage_rate": Decimal("10.0000"),
        "fixed_amount": None,
        "min_fee": Decimal("100.00"),
        "max_fee": Decimal("300.00"),
    }
    assert service.calculate(Decimal("500.00"), rule) == Decimal("100.00")
    assert service.calculate(Decimal("5000.00"), rule) == Decimal("300.00")
