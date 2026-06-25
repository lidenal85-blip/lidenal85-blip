import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

from survey_finder.adapters.base import BaseAdapter, AdapterConfig, AdapterResult
from survey_finder.adapters.http import HTTPClient
from survey_finder.adapters.session import SessionManager
from survey_finder.adapters.errors import AdapterError, AdapterErrorType
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.cycle import CycleContext
from survey_finder.logging.logger import init_logger

logger = init_logger()


class CloudResearchAdapter(BaseAdapter):
    """Adapter for CloudResearch survey platform."""

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.session_manager = SessionManager()
        self.base_url = "https://www.cloudresearch.com"
        self.api_url = "https://api.cloudresearch.com/v1"

    async def initialize(self) -> None:
        """Initialize CloudResearch adapter."""
        logger.info("cloudresearch_initializing")
        session = self.session_manager.get_session("cloudresearch")
        if session:
            logger.info("cloudresearch_session_restored")
        self._is_initialized = True

    async def fetch_surveys(self, context: CycleContext) -> AdapterResult:
        """Fetch available surveys from CloudResearch."""
        logger.info("cloudresearch_fetch_start", cycle_id=context.cycle_id)

        surveys: List[Survey] = []
        errors: List[Dict[str, Any]] = []

        try:
            async with HTTPClient(
                timeout_seconds=self.config.timeout_seconds,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            ) as client:

                response = await client.get(
                    f"{self.api_url}/studies/available"
                )

                if response.status_code == 200:
                    data = response.json()
                    surveys = self._parse_response(data)
                    logger.info("cloudresearch_success", count=len(surveys))
                else:
                    logger.warning("cloudresearch_api_error", status=response.status_code)

        except Exception as e:
            logger.error("cloudresearch_fetch_failed", error=str(e))
            errors.append({
                "source": "cloudresearch",
                "error": str(e),
                "retryable": True
            })

        return AdapterResult(
            source="cloudresearch",
            surveys=surveys,
            errors=errors,
            total_fetched=len(surveys)
        )

    async def close(self) -> None:
        """Close adapter resources."""
        logger.info("cloudresearch_closing")
        self._is_initialized = False

    def _parse_response(self, data: Dict[str, Any]) -> List[Survey]:
        """Parse CloudResearch API response."""
        surveys: List[Survey] = []

        studies = data.get("studies", data.get("results", []))
        for study in studies[:10]:
            try:
                survey = Survey(
                    id=study.get("id", f"cloudresearch_{datetime.utcnow().timestamp()}"),
                    title=study.get("title", study.get("name", "Untitled")),
                    payout=float(study.get("payout", study.get("reward", 0))),
                    duration_minutes=int(study.get("duration_minutes", study.get("duration", 0))),
                    source="cloudresearch"
                )
                surveys.append(survey)
            except (ValueError, TypeError) as e:
                logger.warning("cloudresearch_parse_error", error=str(e))
                continue

        return surveys
