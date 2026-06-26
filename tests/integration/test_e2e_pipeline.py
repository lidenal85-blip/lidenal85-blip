import pytest
import uuid

from survey_finder.pipeline.orchestrator import PipelineOrchestrator
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile
from survey_finder.adapters.base import AdapterConfig, AdapterResult


# ---------------------------------------------------------------------------
# Shared mocks
# ---------------------------------------------------------------------------

class MockAdapter:
    def __init__(self, surveys=None):
        self.config = AdapterConfig(source="mock")
        self._surveys = surveys or [
            Survey(id="t1", title="Survey 1", payout=10.0,
                   duration_minutes=30, source="mock", url="https://example.com/1"),
            Survey(id="t2", title="Survey 2", payout=20.0,
                   duration_minutes=20, source="mock", url="https://example.com/2"),
        ]
    async def initialize(self): pass
    async def fetch_surveys(self, ctx):
        return AdapterResult(source="mock", surveys=self._surveys)
    async def close(self): pass


class ValidNorm:
    def normalize(self, raw, cycle_id):
        from survey_finder.normalization.models import NormalizationResult, NormalizationStatus
        return NormalizationResult(
            status=NormalizationStatus.VALID,
            validated_survey=raw.raw_content,
            validation_errors=[],
        )


class FailNorm:
    def normalize(self, raw, cycle_id):
        from survey_finder.normalization.models import NormalizationResult, NormalizationStatus
        return NormalizationResult(
            status=NormalizationStatus.INVALID,
            validated_survey=None,
            validation_errors=["missing_id"],
        )


class EligibleFilter:
    def evaluate(self, survey, profile, ctx):
        from survey_finder.filter.rules import FilterResult
        import datetime
        return FilterResult(
            decision_id="d1", cycle_id=ctx.cycle_id,
            survey_id=survey.id, status="ELIGIBLE", score=0.9,
            reasons=["country_match", "hourly_rate_ok"],
            generated_at=datetime.datetime.now().isoformat(),
        )


class RejectFilter:
    def evaluate(self, survey, profile, ctx):
        from survey_finder.filter.rules import FilterResult
        import datetime
        return FilterResult(
            decision_id="d1", cycle_id=ctx.cycle_id,
            survey_id=survey.id, status="REJECTED", score=0.1,
            reasons=["FAIL:hourly_rate_too_low"],
            generated_at=datetime.datetime.now().isoformat(),
        )


class AcceptIdempotency:
    def check_and_set(self, key):
        class R:
            status = "ACCEPTED"
        return R()


class DeliveredDispatcher:
    async def dispatch(self, survey, score, reasons):
        return {"status": "DELIVERED", "message_id": "m1"}


class FailDispatcher:
    async def dispatch(self, survey, score, reasons):
        return {"status": "FAILED", "error": "network_error"}


class NullBuffer:
    def push(self, e): return True


class NullDLQ:
    def store(self, i): pass


# aliases for backward-compat imports from test_performance.py
MockNormalizationEngine = ValidNorm
MockFilterEngine = EligibleFilter
MockIdempotencyGate = AcceptIdempotency
MockBuffer = NullBuffer
MockDispatcher = DeliveredDispatcher
MockDLQStorage = NullDLQ


def make_orch(**overrides):
    defaults = dict(
        adapter=MockAdapter(),
        normalization_engine=ValidNorm(),
        filter_engine=EligibleFilter(),
        idempotency_gate=AcceptIdempotency(),
        buffer=NullBuffer(),
        dispatcher=DeliveredDispatcher(),
        dlq_storage=NullDLQ(),
    )
    defaults.update(overrides)
    return PipelineOrchestrator(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_pipeline_success():
    """Both surveys fetched, normalised, eligible, delivered."""
    orch = make_orch()
    cycle_id = str(uuid.uuid4())
    profile = UserProfile(user_id="u1", country="US", min_hourly_rate=5.0)

    result = await orch.run(cycle_id, profile)

    assert result.cycle_id == cycle_id
    assert result.delivered is True          # at least 1 delivered
    assert result.get("fetched") == 2
    assert result.get("delivered") == 2
    assert result.get("errors") == 0


@pytest.mark.asyncio
async def test_e2e_pipeline_with_normalization_failure():
    """Normalization fails → surveys rejected, delivered=0."""
    orch = make_orch(normalization_engine=FailNorm())

    result = await orch.run("cycle-fail-norm")

    assert result.delivered is False
    assert result.get("rejected") == 2
    assert result.get("delivered") == 0


@pytest.mark.asyncio
async def test_e2e_pipeline_filter_rejected():
    """Filter rejects all → nothing delivered."""
    orch = make_orch(filter_engine=RejectFilter())

    result = await orch.run("cycle-rejected")

    assert result.delivered is False
    assert result.get("rejected") == 2
    assert result.get("delivered") == 0


@pytest.mark.asyncio
async def test_e2e_pipeline_dispatch_failure_goes_to_dlq():
    """Dispatch failure increments errors (DLQ'd)."""
    orch = make_orch(dispatcher=FailDispatcher())

    result = await orch.run("cycle-dispatch-fail")

    assert result.delivered is False
    assert result.get("errors") == 2


@pytest.mark.asyncio
async def test_e2e_pipeline_empty_source():
    """No surveys fetched → all counts zero."""
    class EmptyAdapter(MockAdapter):
        async def fetch_surveys(self, ctx):
            return AdapterResult(source="mock", surveys=[])

    orch = make_orch(adapter=EmptyAdapter())
    result = await orch.run("cycle-empty")

    assert result.get("fetched") == 0
    assert result.get("delivered") == 0