from datetime import date, time

import pytest

from app.Modules.Availability.schema import (
    AvailabilityExceptionRequest,
    AvailabilityRuleRequest,
)
from app.Modules.Matching.schema import MatchRequest


def test_availability_rule_requires_valid_time_range():
    with pytest.raises(ValueError):
        AvailabilityRuleRequest(
            day_of_week=1,
            start_time=time(17, 0),
            end_time=time(8, 0),
        )


def test_unavailable_exception_cannot_have_times():
    with pytest.raises(ValueError):
        AvailabilityExceptionRequest(
            exception_date=date(2026, 8, 20),
            is_available=False,
            start_time=time(8, 0),
        )


def test_match_limit_is_bounded():
    with pytest.raises(ValueError):
        MatchRequest(limit=101)
