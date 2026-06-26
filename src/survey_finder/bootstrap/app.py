import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from survey_finder.health.health import router as health_router
from survey_finder.config.settings import settings
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Scheduler singleton
# ---------------------------------------------------------------------------
_scheduler: Optional[AsyncIOScheduler] = None
_last_cycle: dict = {
    "cycle_id": None,
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "summary": {},
}


async def _run_poll_cycle() -> None:
    """Single poll cycle: fetch all sources and run pipeline."""
    global _last_cycle
    cycle_id = str(uuid4())
    _last_cycle.update({"cycle_id": cycle_id, "status": "active",
                        "started_at": datetime.now(timezone.utc).isoformat(),
                        "finished_at": None, "summary": {}})
    logger.info("poll_cycle_start", cycle_id=cycle_id)

    try:
        from survey_finder.bootstrap.pipeline import build_pipeline
        orchestrators = build_pipeline()
        summaries = []
        for orch in orchestrators:
            s = await orch.run(cycle_id)
            summaries.append(s)

        total = {
            "fetched":    sum(s.get("fetched", 0)    for s in summaries),
            "delivered":  sum(s.get("delivered", 0)  for s in summaries),
            "rejected":   sum(s.get("rejected", 0)   for s in summaries),
            "duplicates": sum(s.get("duplicates", 0) for s in summaries),
            "errors":     sum(s.get("errors", 0)     for s in summaries),
        }
        _last_cycle.update({"status": "completed",
                            "finished_at": datetime.now(timezone.utc).isoformat(),
                            "summary": total})
        logger.info("poll_cycle_complete", cycle_id=cycle_id, **total)

    except Exception as e:
        logger.error("poll_cycle_error", cycle_id=cycle_id, error=str(e))
        _last_cycle.update({"status": "failed",
                            "finished_at": datetime.now(timezone.utc).isoformat(),
                            "summary": {"error": str(e)}})


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    logger.info("system_starting",
                poll_interval=settings.POLL_INTERVAL_SECONDS,
                sources=settings.POLL_SOURCES)

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _run_poll_cycle,
        trigger="interval",
        seconds=settings.POLL_INTERVAL_SECONDS,
        id="poll_cycle",
        replace_existing=True,
        max_instances=1,       # never run two cycles in parallel
    )
    _scheduler.start()
    logger.info("scheduler_started",
                interval_sec=settings.POLL_INTERVAL_SECONDS)

    # Run one cycle immediately on startup
    asyncio.create_task(_run_poll_cycle())

    yield  # app is running

    logger.info("system_stopping")
    _scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title="Survey Finder", lifespan=lifespan)
    app.include_router(health_router)

    @app.get("/cycle/status")
    async def cycle_status():
        return _last_cycle

    return app


app = create_app()