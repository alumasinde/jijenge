import pytest
from pydantic import ValidationError

from app.Modules.Locations.schema import ProviderLocationRequest, ServiceAreaRequest


def test_valid_provider_coordinates():
    data = ProviderLocationRequest(
        latitude=-1.286389,
        longitude=36.817223,
        address_line="Nairobi",
    )
    assert data.latitude == -1.286389


def test_invalid_latitude_rejected():
    with pytest.raises(ValidationError):
        ProviderLocationRequest(latitude=100, longitude=36)


def test_service_area_radius_is_bounded():
    with pytest.raises(ValidationError):
        ServiceAreaRequest(
            latitude=-1,
            longitude=36,
            radius_km=501,
        )
