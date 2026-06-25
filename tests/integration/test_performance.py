import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from survey_finder.pipeline.orchestrator import PipelineOrchestrator
from tests.integration.test_e2e_pipeline import (
    MockAdapter, MockNormalizationEngine, MockFilterEngine,
    MockIdempotencyGate, MockBuffer, MockDispatcher, MockDLQStorage
)


def test_pipeline_latency():
    """Test pipeline latency (should be < 1s with mocks)."""
    
    start = time.time()
    
    # Create mock components
    adapter = MockAdapter()
    normalization = MockNormalizationEngine()
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
    
    # Run pipeline
    result = asyncio.run(orchestrator.run("perf-test"))
    
    elapsed = time.time() - start
    
    # Should complete in under 1 second with mocks
    assert elapsed < 1.0
    assert result.delivered is True


def test_pipeline_throughput():
    """Test pipeline can handle multiple cycles."""
    
    def run_cycle(cycle_id):
        adapter = MockAdapter()
        normalization = MockNormalizationEngine()
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
        
        return asyncio.run(orchestrator.run(cycle_id))
    
    # Run 10 cycles
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        cycles = [f"cycle-{i}" for i in range(10)]
        results = list(executor.map(run_cycle, cycles))
    
    elapsed = time.time() - start
    
    # All cycles should complete
    assert len(results) == 10
    assert all(r.delivered for r in results)
    
    # Should handle ~5 cycles per second
    assert elapsed < 5.0
