from decimal import Decimal

from app.Modules.Execution.schema import ExecutionActionRequest, ExecutionLocation


def test_location_bounds():
    data = ExecutionActionRequest(
        location=ExecutionLocation(
            latitude=Decimal("1.2921"),
            longitude=Decimal("36.8219"),
        )
    )
    assert data.location.latitude == Decimal("1.2921")


def test_invalid_latitude():
    try:
        ExecutionLocation(latitude=Decimal("91"), longitude=Decimal("36"))
        assert False
    except ValueError:
        assert True
