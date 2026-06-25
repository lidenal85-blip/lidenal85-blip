import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from survey_finder.adapters.base import BaseAdapter
from survey_finder.normalization.engine import NormalizationEngine
from survey_finder.filter.engine import FilterEngine
from survey_finder.idempotency.gate import RedisIdempotencyGate
from survey_finder.buffer.queue import RedisBuffer
from survey_finder.delivery.dispatcher import TelegramDispatcher
from survey_finder.dlq.storage import DLQStorage
from survey_finder.contracts.user import UserProfile
from survey_finder.pipeline.context import PipelineContext
from survey_finder.pipeline.steps import (
    FetchStep, NormalizeStep, FilterStep, 
    IdempotencyStep, BufferStep, DispatchStep, DLQStep
)
from survey_finder.logging.logger import init_logger

logger = init_logger()


class PipelineOrchestrator:
    """Orchestrates the full pipeline execution."""
    
    def __init__(
        self,
        adapter: BaseAdapter,
        normalization_engine: NormalizationEngine,
        filter_engine: FilterEngine,
        idempotency_gate: RedisIdempotencyGate,
        buffer: RedisBuffer,
        dispatcher: TelegramDispatcher,
        dlq_storage: DLQStorage
    ):
        self.adapter = adapter
        self.normalization_engine = normalization_engine
        self.filter_engine = filter_engine
        self.idempotency_gate = idempotency_gate
        self.buffer = buffer
        self.dispatcher = dispatcher
        self.dlq_storage = dlq_storage
        
        # Initialize steps
        self.steps = [
            FetchStep(adapter),
            NormalizeStep(normalization_engine),
            FilterStep(filter_engine),
            IdempotencyStep(idempotency_gate),
            BufferStep(buffer),
            DispatchStep(dispatcher),
            DLQStep(dlq_storage)
        ]
    
    async def run(
        self,
        cycle_id: str,
        user_profile: Optional[UserProfile] = None
    ) -> PipelineContext:
        """Run the full pipeline."""
        logger.info("pipeline_start", cycle_id=cycle_id)
        
        context = PipelineContext(
            cycle_id=cycle_id,
            user_profile=user_profile or self._default_profile()
        )
        
        # Execute steps sequentially
        for step in self.steps:
            try:
                context = await step.execute(context)
            except Exception as e:
                logger.error("pipeline_step_error",
                            cycle_id=cycle_id,
                            step=step.__class__.__name__,
                            error=str(e))
                context.add_error(step.__class__.__name__, str(e))
                # Continue to next step - DLQ will handle failures
        
        logger.info("pipeline_complete",
                   cycle_id=cycle_id,
                   delivered=context.delivered,
                   errors=len(context.errors))
        
        return context
    
    def _default_profile(self) -> UserProfile:
        """Default user profile for testing."""
        return UserProfile(
            user_id="default",
            country="US",
            min_hourly_rate=15.0
        )
