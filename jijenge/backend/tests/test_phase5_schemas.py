import pytest
from pydantic import ValidationError

from app.Modules.Applications.schema import CreateApplicationRequest
from app.Modules.Jobs.schema import CreateJobRequest


def test_application_price_must_not_be_negative():
    with pytest.raises(ValidationError):
        CreateApplicationRequest(proposed_price=-1)


def test_job_requires_meaningful_description():
    with pytest.raises(ValidationError):
        CreateJobRequest(
            service_id=1,
            title="Fix",
            description="short",
            location={
                "latitude": -1.286389,
                "longitude": 36.817223,
            },
        )
