from typing import Optional

from survey_finder.adapters.registry import AdapterService
from survey_finder.adapters.base import AdapterConfig
from survey_finder.normalization.engine import NormalizationEngine
from survey_finder.filter.engine import FilterEngine
from survey_finder.idempotency.gate import RedisIdempotencyGate
from survey_finder.buffer.queue import RedisBuffer
from survey_finder.delivery.dispatcher import TelegramDispatcher
from survey_finder.dlq.storage import DLQStorage
from survey_finder.pipeline.orchestrator import PipelineOrchestrator
from survey_finder.config.settings import settings
from survey_finder.logging.logger import init_logger

logger = init_logger()


def create_pipeline(
    source: str = "prolific",
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None
) -> PipelineOrchestrator:
    """Create a configured pipeline orchestrator."""
    
    # Adapter
    config = AdapterConfig(source=source, timeout_seconds=30)
    adapter = AdapterService().get_adapter(source, config)
    
    # Engine components
    normalization_engine = NormalizationEngine(strict=True)
    filter_engine = FilterEngine(min_score=0.5)
    idempotency_gate = RedisIdempotencyGate(ttl_seconds=86400)
    buffer = RedisBuffer()
    dlq_storage = DLQStorage()
    
    # Telegram dispatcher
    bot_token = bot_token or getattr(settings, "TELEGRAM_BOT_TOKEN", "test_token")
    chat_id = chat_id or getattr(settings, "TELEGRAM_CHAT_ID", "test_chat")
    
    dispatcher = TelegramDispatcher(
        bot_token=bot_token,
        chat_id=chat_id,
        buffer=buffer,
        idempotency_gate=idempotency_gate
    )
    
    # Create orchestrator
    return PipelineOrchestrator(
        adapter=adapter,
        normalization_engine=normalization_engine,
        filter_engine=filter_engine,
        idempotency_gate=idempotency_gate,
        buffer=buffer,
        dispatcher=dispatcher,
        dlq_storage=dlq_storage
    )


async def run_pipeline(
    source: str = "prolific",
    cycle_id: Optional[str] = None
) -> None:
    """Run the pipeline once."""
    import uuid
    cycle_id = cycle_id or str(uuid.uuid4())
    
    pipeline = create_pipeline(source)
    await pipeline.initialize()
    
    try:
        result = await pipeline.run(cycle_id)
        logger.info("pipeline_run_complete",
                   cycle_id=cycle_id,
                   delivered=result.delivered,
                   errors=len(result.errors))
        return result
    finally:
        await pipeline.close()
