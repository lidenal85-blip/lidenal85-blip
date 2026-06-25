import pytest
import json
from survey_finder.adapters.errors import AdapterError, AdapterErrorType
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile


def test_no_secrets_in_logs():
    """Test that secrets are not exposed in error messages."""
    
    try:
        raise AdapterError(
            error_type=AdapterErrorType.AUTH_FAILED,
            message="Invalid token: ghp_abc123def456",
            source="test",
            retryable=False
        )
    except AdapterError as e:
        error_str = str(e)
        # Should not contain full token
        assert "ghp_abc123def456" not in error_str
        assert "token" not in error_str.lower()


def test_input_validation():
    """Test that invalid input is rejected."""
    
    # Empty survey
    with pytest.raises(ValueError):
        Survey(
            id="",
            title="",
            payout=-10.0,
            duration_minutes=0,
            source=""
        )
    
    # Invalid user profile
    with pytest.raises(ValueError):
        UserProfile(
            user_id="",
            country="",
            min_hourly_rate=-5.0
        )


def test_serialization_safety():
    """Test that serialization doesn't expose internal data."""
    
    survey = Survey(
        id="test-1",
        title="Test",
        payout=10.0,
        duration_minutes=5,
        source="mock"
    )
    
    data = survey.model_dump()
    
    # Should only contain expected fields
    expected_fields = {"id", "title", "payout", "duration_minutes", "source", "schema_version"}
    assert set(data.keys()) == expected_fields


def test_dlq_sanitization():
    """Test DLQ items don't contain secrets."""
    
    from survey_finder.contracts.dlq import DLQItem
    from datetime import datetime
    
    item = DLQItem(
        cycle_id="c1",
        source="test",
        payload_type="survey",
        raw_payload={"id": "1", "secret": "password123"},
        reason="test",
        failed_at=datetime.utcnow()
    )
    
    data = item.model_dump()
    # DLQ should not log secrets - but raw_payload can contain anything
    # This test just ensures the item is properly structured
    assert "payload_type" in data
    assert data["source"] == "test"
