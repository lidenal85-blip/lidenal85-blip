import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from survey_finder.adapters.base import BaseAdapter, AdapterResult
from survey_finder.normalization.engine import NormalizationEngine
from survey_finder.normalization.models import RawPayload, NormalizationStatus
from survey_finder.filter.engine import FilterEngine
from survey_finder.idempotency.gate import RedisIdempotencyGate
from survey_finder.buffer.queue import RedisBuffer
from survey_finder.delivery.dispatcher import TelegramDispatcher
from survey_finder.dlq.storage import DLQStorage
from survey_finder.contracts.dlq import DLQItem
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile
from survey_finder.contracts.cycle import CycleContext
from survey_finder.pipeline.context import PipelineContext
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class FetchStep:
    """Step 1: Fetch surveys from adapter."""
    
    def __init__(self, adapter: BaseAdapter):
        self.adapter = adapter
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        logger.info("pipeline_fetch", cycle_id=context.cycle_id)
        
        try:
            result = await self.adapter.fetch_surveys(
                CycleContext(cycle_id=context.cycle_id)
            )
            
            if result.surveys:
                # Create raw payload from first survey
                survey = result.surveys[0]
                context.raw_payload = RawPayload(
                    payload_id=f"raw_{survey.id}",
                    source=result.source,
                    fetched_at=result.fetched_at,
                    source_schema_version="v1",
                    raw_content=survey.model_dump(),
                    metadata={"total_fetched": result.total_fetched}
                )
                logger.info("pipeline_fetch_success", 
                           cycle_id=context.cycle_id,
                           count=result.total_fetched)
            else:
                logger.info("pipeline_fetch_empty", cycle_id=context.cycle_id)
                
        except Exception as e:
            logger.error("pipeline_fetch_failed", cycle_id=context.cycle_id, error=str(e))
            context.add_error("fetch", str(e))
        
        return context


class NormalizeStep:
    """Step 2: Normalize raw payload."""
    
    def __init__(self, engine: NormalizationEngine):
        self.engine = engine
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.raw_payload:
            context.add_error("normalize", "No raw payload to normalize")
            return context
        
        logger.info("pipeline_normalize", cycle_id=context.cycle_id)
        
        try:
            result = self.engine.normalize(
                context.raw_payload,
                context.cycle_id
            )
            
            context.normalization_result = result
            
            if result.status == NormalizationStatus.VALID:
                context.survey = Survey(**result.validated_survey)
                logger.info("pipeline_normalize_success", 
                           cycle_id=context.cycle_id,
                           survey_id=context.survey.id)
            elif result.status == NormalizationStatus.PARTIAL:
                logger.warning("pipeline_normalize_partial",
                              cycle_id=context.cycle_id,
                              warnings=result.warnings)
                if result.validated_survey:
                    context.survey = Survey(**result.validated_survey)
            else:
                logger.warning("pipeline_normalize_failed",
                              cycle_id=context.cycle_id,
                              errors=result.validation_errors)
                context.add_error("normalize", 
                                 f"Validation failed: {result.validation_errors}")
                
        except Exception as e:
            logger.error("pipeline_normalize_error", cycle_id=context.cycle_id, error=str(e))
            context.add_error("normalize", str(e))
        
        return context


class FilterStep:
    """Step 3: Filter survey against user profile."""
    
    def __init__(self, engine: FilterEngine):
        self.engine = engine
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.survey:
            context.add_error("filter", "No survey to filter")
            return context
        
        if not context.user_profile:
            context.add_error("filter", "No user profile available")
            return context
        
        logger.info("pipeline_filter", cycle_id=context.cycle_id)
        
        try:
            result = self.engine.evaluate(
                context.survey,
                context.user_profile,
                CycleContext(cycle_id=context.cycle_id)
            )
            
            context.filter_result = result
            
            if result.status == "ELIGIBLE":
                logger.info("pipeline_filter_eligible",
                           cycle_id=context.cycle_id,
                           survey_id=context.survey.id,
                           score=result.score)
            else:
                logger.info("pipeline_filter_rejected",
                           cycle_id=context.cycle_id,
                           survey_id=context.survey.id,
                           status=result.status,
                           reasons=result.reasons)
                
        except Exception as e:
            logger.error("pipeline_filter_error", cycle_id=context.cycle_id, error=str(e))
            context.add_error("filter", str(e))
        
        return context


class IdempotencyStep:
    """Step 4: Check idempotency."""
    
    def __init__(self, gate: RedisIdempotencyGate):
        self.gate = gate
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.survey or not context.filter_result:
            return context
        
        if context.filter_result.status != "ELIGIBLE":
            return context
        
        logger.info("pipeline_idempotency", cycle_id=context.cycle_id)
        
        try:
            key = f"survey:{context.survey.id}"
            result = self.gate.check_and_set(key)
            
            if result.status == "DUPLICATE":
                logger.info("pipeline_duplicate_skipped",
                           cycle_id=context.cycle_id,
                           survey_id=context.survey.id)
                context.survey = None  # Skip duplicate
            else:
                logger.info("pipeline_idempotency_accepted",
                           cycle_id=context.cycle_id,
                           survey_id=context.survey.id)
                
        except Exception as e:
            logger.warning("pipeline_idempotency_error",
                          cycle_id=context.cycle_id,
                          error=str(e))
            # Continue anyway - idempotency is best-effort
        
        return context


class BufferStep:
    """Step 5: Push to buffer."""
    
    def __init__(self, buffer: RedisBuffer):
        self.buffer = buffer
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.survey or not context.filter_result:
            return context
        
        if context.filter_result.status != "ELIGIBLE":
            return context
        
        logger.info("pipeline_buffer", cycle_id=context.cycle_id)
        
        try:
            event = {
                "type": "survey_notification",
                "cycle_id": context.cycle_id,
                "survey": context.survey.model_dump(),
                "score": context.filter_result.score,
                "reasons": context.filter_result.reasons
            }
            
            pushed = self.buffer.push(event)
            
            if pushed:
                logger.info("pipeline_buffer_success",
                           cycle_id=context.cycle_id,
                           survey_id=context.survey.id)
            else:
                logger.warning("pipeline_buffer_full",
                              cycle_id=context.cycle_id,
                              survey_id=context.survey.id)
                context.add_error("buffer", "Buffer full, backpressure applied")
                
        except Exception as e:
            logger.error("pipeline_buffer_error", cycle_id=context.cycle_id, error=str(e))
            context.add_error("buffer", str(e))
        
        return context


class DispatchStep:
    """Step 6: Dispatch to Telegram."""
    
    def __init__(self, dispatcher: TelegramDispatcher):
        self.dispatcher = dispatcher
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.survey or not context.filter_result:
            return context
        
        if context.filter_result.status != "ELIGIBLE":
            return context
        
        logger.info("pipeline_dispatch", cycle_id=context.cycle_id)
        
        try:
            result = await self.dispatcher.dispatch(
                context.survey.model_dump(),
                context.filter_result.score,
                context.filter_result.reasons
            )
            
            if result.get("status") == "DELIVERED":
                context.delivered = True
                logger.info("pipeline_dispatch_success",
                           cycle_id=context.cycle_id,
                           survey_id=context.survey.id)
            else:
                logger.warning("pipeline_dispatch_failed",
                              cycle_id=context.cycle_id,
                              survey_id=context.survey.id,
                              error=result.get("error"))
                context.add_error("dispatch", result.get("error", "Unknown error"))
                
        except Exception as e:
            logger.error("pipeline_dispatch_error", cycle_id=context.cycle_id, error=str(e))
            context.add_error("dispatch", str(e))
        
        return context


class DLQStep:
    """Step 7: Push to DLQ on failure."""
    
    def __init__(self, storage: DLQStorage):
        self.storage = storage
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.errors:
            return context
        
        if context.delivered:
            return context
        
        logger.info("pipeline_dlq", cycle_id=context.cycle_id)
        
        try:
            for error in context.errors:
                dlq_item = DLQItem(
                    cycle_id=context.cycle_id,
                    source=context.raw_payload.source if context.raw_payload else "unknown",
                    payload_type="survey",
                    raw_payload=context.survey.model_dump() if context.survey else {},
                    reason=f"{error['step']}: {error['error']}",
                    failed_at=datetime.utcnow()
                )
                self.storage.store(dlq_item)
                logger.info("pipeline_dlq_stored",
                           cycle_id=context.cycle_id,
                           step=error['step'])
                
        except Exception as e:
            logger.error("pipeline_dlq_error", cycle_id=context.cycle_id, error=str(e))
        
        return context
