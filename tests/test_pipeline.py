import pytest
from unittest.mock import AsyncMock, MagicMock
from survey_finder.pipeline.context import PipelineContext
from survey_finder.pipeline.steps import (
    FetchStep, NormalizeStep, FilterStep,
    IdempotencyStep, BufferStep, DispatchStep, DLQStep
)
from survey_finder.adapters.base import AdapterConfig, AdapterResult
from survey_finder.normalization.engine import NormalizationEngine
from survey_finder.filter.engine import FilterEngine
from survey_finder.idempotency.gate import RedisIdempotencyGate
from survey_finder.buffer.queue import RedisBuffer
from survey_finder.dlq.storage import DLQStorage
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile


def test_pipeline_context():
    context = PipelineContext(cycle_id="test-1")
    assert context.cycle_id == "test-1"
    assert context.errors == []
    assert context.delivered is False


def test_fetch_step():
    """Test fetch step can be created."""
    from survey_finder.adapters.prolific.adapter import ProlificAdapter
    config = AdapterConfig(source="prolific")
    adapter = ProlificAdapter(config)
    
    step = FetchStep(adapter)
    assert step.adapter.source_name == "prolific"


def test_normalize_step():
    engine = NormalizationEngine()
    step = NormalizeStep(engine)
    assert step.engine is not None


def test_filter_step():
    engine = FilterEngine()
    step = FilterStep(engine)
    assert step.engine is not None


def test_idempotency_step():
    gate = RedisIdempotencyGate(ttl_seconds=60)
    step = IdempotencyStep(gate)
    assert step.gate is not None


def test_buffer_step():
    buffer = RedisBuffer()
    step = BufferStep(buffer)
    assert step.buffer is not None


def test_dlq_step():
    storage = DLQStorage()
    step = DLQStep(storage)
    assert step.storage is not None
