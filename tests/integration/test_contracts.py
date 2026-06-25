import pytest
from survey_finder.contracts.cep import CycleExecutionProtocol
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile
from survey_finder.contracts.dlq import DLQItem
from survey_finder.contracts.errors import ErrorEvent, ErrorType
from survey_finder.contracts.versioning import CURRENT_CONTRACT_VERSION
from datetime import datetime


def test_all_contracts_versioned():
    """Test that all contracts have version fields."""
    
    survey = Survey(
        id="test",
        title="Test",
        payout=10.0,
        duration_minutes=5,
        source="test"
    )
    assert hasattr(survey, "schema_version")
    assert survey.schema_version == "v1"
    
    user = UserProfile(user_id="u1", country="US")
    assert hasattr(user, "profile_version")
    assert user.profile_version == "v1"
    
    cycle = CycleExecutionProtocol()
    assert hasattr(cycle, "version")
    assert cycle.version == CURRENT_CONTRACT_VERSION.value


def test_dlq_contract():
    """Test DLQ contract structure."""
    
    item = DLQItem(
        cycle_id="c1",
        source="test",
        payload_type="survey",
        raw_payload={},
        reason="test",
        failed_at=datetime.utcnow()
    )
    
    # Required fields
    assert item.cycle_id == "c1"
    assert item.source == "test"
    assert item.payload_type == "survey"
    assert item.reason == "test"


def test_error_contract():
    """Test error contract structure."""
    
    error = ErrorEvent(
        cycle_id="c1",
        source="test",
        error_type=ErrorType.INTERNAL_FAILURE,
        message="Something went wrong",
        timestamp=datetime.utcnow(),
        retryable=True
    )
    
    assert error.cycle_id == "c1"
    assert error.retryable is True
    assert error.error_type == ErrorType.INTERNAL_FAILURE


def test_idempotency_contract():
    """Test idempotency contract structure."""
    
    from survey_finder.contracts.idempotency import IdempotencyKey
    
    key = IdempotencyKey(
        key="test:123",
        entity_type="survey",
        created_at=datetime.utcnow()
    )
    
    assert key.key == "test:123"
    assert key.entity_type == "survey"
