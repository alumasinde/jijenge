import pytest
from pydantic import ValidationError
from app.Modules.JobLifecycle.schema import JobTransitionRequest

def test_transition_notes_trim():
    assert JobTransitionRequest(notes="  arrived  ").notes == "arrived"

def test_transition_reason_limit():
    with pytest.raises(ValidationError):
        JobTransitionRequest(cancellation_reason="x"*1001)
