from typing import List

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
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


def _make_orchestrator(source: str) -> PipelineOrchestrator:
    """Build one PipelineOrchestrator for a given source."""
    config = AdapterConfig(source=source, timeout_seconds=30)
    adapter = AdapterService().get_adapter(source, config)

    idempotency_gate = RedisIdempotencyGate(ttl_seconds=86400)
    buffer = RedisBuffer()

    dispatcher = TelegramDispatcher(
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        chat_id=settings.TELEGRAM_CHAT_ID,
        buffer=buffer,
        idempotency_gate=idempotency_gate,
    )

    return PipelineOrchestrator(
        adapter=adapter,
        normalization_engine=NormalizationEngine(strict=True),
        filter_engine=FilterEngine(min_score=0.5),
        idempotency_gate=idempotency_gate,
        buffer=buffer,
        dispatcher=dispatcher,
        dlq_storage=DLQStorage(),
    )


def build_pipeline() -> List[PipelineOrchestrator]:
    """
    Build one orchestrator per enabled source.
    Sources come from settings.POLL_SOURCES (comma-separated).
    """
    sources = [s.strip() for s in settings.POLL_SOURCES.split(",") if s.strip()]
    orchestrators = []
    for source in sources:
        try:
            orch = _make_orchestrator(source)
            orchestrators.append(orch)
            logger.info("pipeline_built", source=source)
        except Exception as e:
            logger.error("pipeline_build_error", source=source, error=str(e))
    return orchestrators


async def run_pipeline_once(cycle_id: str | None = None) -> dict:
    """Convenience: run one full cycle across all sources."""
    import asyncio
    from uuid import uuid4
    cycle_id = cycle_id or str(uuid4())
    orchestrators = build_pipeline()
    results = await asyncio.gather(
        *[o.run(cycle_id) for o in orchestrators],
        return_exceptions=True,
    )
    totals: dict = {"fetched": 0, "delivered": 0, "rejected": 0,
                   "duplicates": 0, "errors": 0}
    for r in results:
        if isinstance(r, dict):
            for k in totals:
                totals[k] += r.get(k, 0)
        else:
            totals["errors"] += 1
    logger.info("run_pipeline_once_done", cycle_id=cycle_id, **totals)
    return totals