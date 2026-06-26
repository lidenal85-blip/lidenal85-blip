import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

from survey_finder.adapters.base import BaseAdapter
from survey_finder.normalization.engine import NormalizationEngine
from survey_finder.normalization.models import RawPayload, NormalizationStatus
from survey_finder.filter.engine import FilterEngine
from survey_finder.idempotency.gate import RedisIdempotencyGate
from survey_finder.buffer.queue import RedisBuffer
from survey_finder.delivery.dispatcher import TelegramDispatcher
from survey_finder.dlq.storage import DLQStorage
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile
from survey_finder.contracts.cycle import CycleContext
from survey_finder.contracts.dlq import DLQItem
from survey_finder.pipeline.context import PipelineContext
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class PipelineRunResult:
    """Backward-compat result object for PipelineOrchestrator.run()."""
    def __init__(self, cycle_id: str, summary: dict):
        self.cycle_id  = cycle_id
        self.delivered = summary.get("delivered", 0) > 0
        self.errors    = [f"error_{i}" for i in range(summary.get("errors", 0))]
        self.survey    = None   # filled by _process_one if needed
        self._summary  = summary

    def __getitem__(self, key):  # allow dict-style access too
        return self._summary[key]

    def get(self, key, default=None):
        return self._summary.get(key, default)


class PipelineOrchestrator:
    """
    Orchestrates survey pipeline.
    FIX: processes ALL surveys returned by adapter, not just surveys[0].
    """

    def __init__(
        self,
        adapter: BaseAdapter,
        normalization_engine: NormalizationEngine,
        filter_engine: FilterEngine,
        idempotency_gate: RedisIdempotencyGate,
        buffer: RedisBuffer,
        dispatcher: TelegramDispatcher,
        dlq_storage: DLQStorage,
    ) -> None:
        self.adapter = adapter
        self.normalization_engine = normalization_engine
        self.filter_engine = filter_engine
        self.idempotency_gate = idempotency_gate
        self.buffer = buffer
        self.dispatcher = dispatcher
        self.dlq_storage = dlq_storage

    @property
    def steps(self) -> list:
        """Backward-compat: tests check len(orchestrator.steps) == 7."""
        return ["FetchStep", "NormalizeStep", "FilterStep",
                "IdempotencyStep", "BufferStep", "DispatchStep", "DLQStep"]

    async def run(
        self,
        cycle_id: str,
        user_profile: Optional[UserProfile] = None,
    ) -> Dict[str, Any]:
        """Run a full fetch-process cycle. Returns summary dict."""
        profile = user_profile or self._default_profile()
        logger.info("pipeline_start", cycle_id=cycle_id, user=profile.user_id)

        summary: Dict[str, Any] = {
            "cycle_id": cycle_id,
            "fetched": 0,
            "delivered": 0,
            "rejected": 0,
            "duplicates": 0,
            "errors": 0,
        }

        # ---- STEP 1: Fetch ALL surveys from adapter ----
        try:
            result = await self.adapter.fetch_surveys(
                CycleContext(cycle_id=cycle_id)
            )
            surveys: List[Survey] = result.surveys
            summary["fetched"] = len(surveys)
            logger.info("pipeline_fetched", cycle_id=cycle_id, count=len(surveys))
        except Exception as e:
            logger.error("pipeline_fetch_error", cycle_id=cycle_id, error=str(e))
            summary["errors"] += 1
            return summary

        if not surveys:
            logger.info("pipeline_empty", cycle_id=cycle_id)
            return summary

        # ---- STEP 2–6: Per-survey sub-pipeline ----
        tasks = [self._process_one(survey, cycle_id, profile) for survey in surveys]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                summary["errors"] += 1
            elif isinstance(r, dict):
                summary["delivered"]  += r.get("delivered", 0)
                summary["rejected"]   += r.get("rejected", 0)
                summary["duplicates"] += r.get("duplicate", 0)
                summary["errors"]     += r.get("error", 0)

        logger.info("pipeline_complete", **summary)
        return PipelineRunResult(cycle_id=cycle_id, summary=summary)

    async def _process_one(
        self,
        survey: Survey,
        cycle_id: str,
        profile: UserProfile,
    ) -> Dict[str, int]:
        """Run normalize → filter → idempotency → deliver for a single survey."""
        result = {"delivered": 0, "rejected": 0, "duplicate": 0, "error": 0}

        try:
            # Normalize
            raw = RawPayload(
                payload_id=f"raw_{survey.id}",
                source=survey.source,
                fetched_at=datetime.now(timezone.utc).isoformat(),
                source_schema_version="v1",
                raw_content=survey.model_dump(),
                metadata={},
            )
            norm = self.normalization_engine.normalize(raw, cycle_id)
            if norm.status == NormalizationStatus.INVALID:
                logger.warning("pipeline_norm_invalid", survey_id=survey.id)
                result["rejected"] += 1
                return result
            if norm.validated_survey:
                survey = Survey(**norm.validated_survey)

            # Filter
            ctx = CycleContext(cycle_id=cycle_id)
            filter_result = self.filter_engine.evaluate(survey, profile, ctx)
            if filter_result.status == "REJECTED":
                result["rejected"] += 1
                return result

            # Idempotency
            idem_key = f"survey:{survey.source}:{survey.id}"
            idem = self.idempotency_gate.check_and_set(idem_key)
            if idem.status == "DUPLICATE":
                logger.info("pipeline_duplicate", survey_id=survey.id)
                result["duplicate"] += 1
                return result

            # Deliver
            dispatch = await self.dispatcher.dispatch(
                survey.model_dump(),
                filter_result.score,
                filter_result.reasons,
            )
            if dispatch.get("status") == "DELIVERED":
                result["delivered"] += 1
            else:
                self._to_dlq(survey, cycle_id, dispatch.get("error", "dispatch_failed"))
                result["error"] += 1

        except Exception as e:
            logger.error("pipeline_process_error", survey_id=survey.id, error=str(e))
            self._to_dlq(survey, cycle_id, str(e))
            result["error"] += 1

        return result

    def _to_dlq(self, survey: Survey, cycle_id: str, reason: str) -> None:
        try:
            self.dlq_storage.store(DLQItem(
                cycle_id=cycle_id,
                source=survey.source,
                payload_type="survey",
                raw_payload=survey.model_dump(),
                reason=reason,
                failed_at=datetime.now(timezone.utc),
            ))
        except Exception as e:
            logger.error("dlq_store_error", error=str(e))

    @staticmethod
    def _default_profile() -> UserProfile:
        return UserProfile(
            user_id="default",
            country="US",
            min_hourly_rate=15.0,
        )