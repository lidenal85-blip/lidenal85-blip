import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from survey_finder.pipeline.orchestrator import PipelineOrchestrator
from survey_finder.pipeline.context import PipelineContext
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile
from survey_finder.contracts.cycle import CycleContext
from survey_finder.adapters.base import AdapterConfig, AdapterResult


class MockAdapter:
    """Mock adapter for testing."""
    
    def __init__(self, config=None):
        self.config = config or AdapterConfig(source="mock")
        self._is_initialized = True
        self.source_name = "mock"
        
    async def initialize(self):
        self._is_initialized = True
        
    async def fetch_surveys(self, context):
        return AdapterResult(
            source="mock",
            surveys=[
                Survey(
                    id="test-1",
                    title="Test Survey 1",
                    payout=10.0,
                    duration_minutes=5,
                    source="mock"
                ),
                Survey(
                    id="test-2",
                    title="Test Survey 2",
                    payout=20.0,
                    duration_minutes=10,
                    source="mock"
                )
            ]
        )
        
    async def close(self):
        self._is_initialized = False


class MockNormalizationEngine:
    def normalize(self, raw_payload, cycle_id):
        from survey_finder.normalization.models import NormalizationResult, NormalizationStatus
        return NormalizationResult(
            status=NormalizationStatus.VALID,
            validated_survey=raw_payload.raw_content,
            validation_errors=[]
        )


class MockFilterEngine:
    def evaluate(self, survey, profile, context):
        from survey_finder.filter.engine import FilterResult
        return FilterResult(
            decision_id="dec-1",
            cycle_id=context.cycle_id,
            survey_id=survey.id,
            status="ELIGIBLE",
            score=0.8,
            reasons=["country_match", "hourly_rate_ok"],
            generated_at="2026-01-01T00:00:00"
        )


class MockIdempotencyGate:
    def check_and_set(self, key):
        class Result:
            status = "ACCEPTED"
            idempotency_key = key
        return Result()


class MockBuffer:
    def push(self, event):
        return True


class MockDispatcher:
    async def dispatch(self, survey, score, reasons):
        return {"status": "DELIVERED", "message_id": "msg-1"}


class MockDLQStorage:
    def store(self, item):
        pass


@pytest.mark.asyncio
async def test_e2e_pipeline_success():
    """Test full pipeline with all mocks."""
    
    # Create mock components
    adapter = MockAdapter()
    normalization = MockNormalizationEngine()
    filter_engine = MockFilterEngine()
    idempotency = MockIdempotencyGate()
    buffer = MockBuffer()
    dispatcher = MockDispatcher()
    dlq = MockDLQStorage()
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        adapter=adapter,
        normalization_engine=normalization,
        filter_engine=filter_engine,
        idempotency_gate=idempotency,
        buffer=buffer,
        dispatcher=dispatcher,
        dlq_storage=dlq
    )
    
    # Run pipeline
    cycle_id = str(uuid.uuid4())
    profile = UserProfile(
        user_id="test-user",
        country="US",
        min_hourly_rate=15.0
    )
    
    result = await orchestrator.run(cycle_id, profile)
    
    # Assertions
    assert result.cycle_id == cycle_id
    assert result.delivered is True
    assert len(result.errors) == 0
    assert result.survey is not None


@pytest.mark.asyncio
async def test_e2e_pipeline_with_normalization_failure():
    """Test pipeline when normalization fails."""
    
    from survey_finder.normalization.models import NormalizationResult, NormalizationStatus
    
    class FailingNormalizationEngine:
        def normalize(self, raw_payload, cycle_id):
            return NormalizationResult(
                status=NormalizationStatus.INVALID,
                validated_survey=None,
                validation_errors=["Missing required field: id"],
                warnings=[]
            )
    
    # Create mocks
    adapter = MockAdapter()
    normalization = FailingNormalizationEngine()
    filter_engine = MockFilterEngine()
    idempotency = MockIdempotencyGate()
    buffer = MockBuffer()
    dispatcher = MockDispatcher()
    dlq = MockDLQStorage()
    
    orchestrator = PipelineOrchestrator(
        adapter=adapter,
        normalization_engine=normalization,
        filter_engine=filter_engine,
        idempotency_gate=idempotency,
        buffer=buffer,
        dispatcher=dispatcher,
        dlq_storage=dlq
    )
    
    result = await orchestrator.run("cycle-1")
    
    # Should have errors
    assert len(result.errors) > 0
    assert result.delivered is False


@pytest.mark.asyncio
async def test_e2e_pipeline_filter_rejected():
    """Test pipeline when filter rejects survey."""
    
    class RejectingFilterEngine:
        def evaluate(self, survey, profile, context):
            from survey_finder.filter.engine import FilterResult
            return FilterResult(
                decision_id="dec-2",
                cycle_id=context.cycle_id,
                survey_id=survey.id,
                status="REJECTED",
                score=0.1,
                reasons=["country_mismatch", "hourly_rate_too_low"],
                generated_at="2026-01-01T00:00:00"
            )
    
    # Create mocks
    adapter = MockAdapter()
    normalization = MockNormalizationEngine()
    filter_engine = RejectingFilterEngine()
    idempotency = MockIdempotencyGate()
    buffer = MockBuffer()
    dispatcher = MockDispatcher()
    dlq = MockDLQStorage()
    
    orchestrator = PipelineOrchestrator(
        adapter=adapter,
        normalization_engine=normalization,
        filter_engine=filter_engine,
        idempotency_gate=idempotency,
        buffer=buffer,
        dispatcher=dispatcher,
        dlq_storage=dlq
    )
    
    result = await orchestrator.run("cycle-1")
    
    # Should be delivered (filter rejection doesn't stop pipeline)
    assert result.delivered is False  # Filter rejected, so no delivery
    assert result.filter_result.status == "REJECTED"
