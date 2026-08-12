from app.Modules.Auth.schema import RegisterRequest
from app.Modules.Providers.schema import AddProviderServiceRequest


def test_register_requires_first_and_last_name():
    data = RegisterRequest(
        first_name=" Jane ",
        last_name=" Doe ",
        email="jane@example.com",
        password="a-very-long-secure-password",
    )
    assert data.first_name == "Jane"
    assert data.last_name == "Doe"


def test_provider_service_price_range():
    data = AddProviderServiceRequest(
        service_id=1,
        minimum_price=500,
        maximum_price=1500,
    )
    assert data.maximum_price >= data.minimum_price
