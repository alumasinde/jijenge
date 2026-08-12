import pytest
from pydantic import ValidationError

from app.Modules.Notifications.schema import RegisterDeviceTokenRequest


def test_device_token_requires_platform():
    with pytest.raises(ValidationError):
        RegisterDeviceTokenRequest(
            platform="",
            token="a-valid-looking-device-token",
        )


def test_device_token_schema():
    data = RegisterDeviceTokenRequest(
        platform="android",
        token="device-token-123456789",
        device_name="Android phone",
        app_version="1.0.0",
    )
    assert data.platform == "android"
