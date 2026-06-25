import pytest
from survey_finder.pipeline.orchestrator import PipelineOrchestrator
from survey_finder.contracts.user import UserProfile


def test_pipeline_creation():
    """Test pipeline orchestrator can be created with mocks."""
    from unittest.mock import MagicMock
    
    adapter = MagicMock()
    normalization = MagicMock()
    filter_engine = MagicMock()
    idempotency = MagicMock()
    buffer = MagicMock()
    dispatcher = MagicMock()
    dlq = MagicMock()
    
    orchestrator = PipelineOrchestrator(
        adapter=adapter,
        normalization_engine=normalization,
        filter_engine=filter_engine,
        idempotency_gate=idempotency,
        buffer=buffer,
        dispatcher=dispatcher,
        dlq_storage=dlq
    )
    
    assert orchestrator is not None
    assert len(orchestrator.steps) == 7  # Fetch, Normalize, Filter, Idempotency, Buffer, Dispatch, DLQ


def test_default_profile():
    """Test default user profile."""
    profile = UserProfile(
        user_id="default",
        country="US",
        min_hourly_rate=15.0
    )
    assert profile.country == "US"
    assert profile.min_hourly_rate == 15.0
