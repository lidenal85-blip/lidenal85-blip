from typing import Dict, Any, List
from datetime import datetime, timezone

from survey_finder.adapters.base import BaseAdapter, AdapterConfig, AdapterResult
from survey_finder.adapters.http import HTTPClient
from survey_finder.adapters.nimble import NimbleClient
from survey_finder.hardening.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.cycle import CycleContext
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)

BASE_URL  = "https://www.respondent.io"
API_URL   = "https://api.respondent.io/v1"
STUDY_URL = "https://app.respondent.io/projects/{id}"


class RespondentAdapter(BaseAdapter):
    """Adapter for Respondent.io — API first, Nimble scrape as fallback."""

    def __init__(self, config: AdapterConfig) -> None:
        super().__init__(config)
        self._nimble = NimbleClient()
        self._cb = CircuitBreaker(name="respondent", config=CircuitBreakerConfig(failure_threshold=3, timeout_seconds=120))

    async def initialize(self) -> None:
        logger.info("respondent_initializing")
        self._is_initialized = True

    async def fetch_surveys(self, context: CycleContext) -> AdapterResult:
        logger.info("respondent_fetch_start", cycle_id=context.cycle_id)
        surveys: List[Survey] = []
        errors:  List[Dict[str, Any]] = []

        try:
            api_surveys = await self._cb.async_call(self._fetch_via_api, context)
            surveys.extend(api_surveys)
            logger.info("respondent_api_ok", count=len(api_surveys))
        except Exception as e:
            logger.warning("respondent_api_failed", error=str(e))
            errors.append({"source": "respondent", "stage": "api", "error": str(e), "retryable": True})

        if not surveys and self._nimble.enabled:
            try:
                nimble_surveys = await self._fetch_via_nimble(context)
                surveys.extend(nimble_surveys)
                logger.info("respondent_nimble_ok", count=len(nimble_surveys))
            except Exception as e:
                logger.warning("respondent_nimble_failed", error=str(e))
                errors.append({"source": "respondent", "stage": "nimble", "error": str(e), "retryable": True})

        return AdapterResult(source="respondent", surveys=surveys, errors=errors, total_fetched=len(surveys))

    async def close(self) -> None:
        self._is_initialized = False

    async def _fetch_via_api(self, context: CycleContext) -> List[Survey]:
        headers = {"Accept": "application/json",
                   "User-Agent": "Mozilla/5.0 (compatible; SurveyFinder/1.0)"}
        async with HTTPClient(timeout_seconds=self.config.timeout_seconds, headers=headers) as client:
            resp = await client.get(f"{API_URL}/projects/open")
            if resp.status_code == 200:
                return self._parse_api(resp.json())
            logger.warning("respondent_api_status", status=resp.status_code)
            return []

    async def _fetch_via_nimble(self, context: CycleContext) -> List[Survey]:
        html = await self._nimble.fetch_html(f"{BASE_URL}/projects", render_js=True)
        if not html:
            return []
        return self._parse_html(html)

    def _parse_api(self, data: Dict[str, Any]) -> List[Survey]:
        surveys = []
        for s in data.get("studies", data.get("data", data.get("projects", [])))[:20]:
            try:
                sid = str(s.get("id", self._ts()))
                surveys.append(Survey(
                    id=sid,
                    title=s.get("title", s.get("name", "Untitled")),
                    payout=float(s.get("payout", s.get("compensation", 0))),
                    duration_minutes=int(s.get("duration_minutes", s.get("duration", 0))),
                    source="respondent",
                    url=STUDY_URL.format(id=sid),
                    description=s.get("description", ""),
                    places_available=s.get("spots_remaining", None),
                    deadline=s.get("closes_at", s.get("deadline", None)),
                    device_requirements=s.get("device_requirements", []),
                    country=s.get("country", None),
                    eligibility_criteria=s.get("screener", {}),
                ))
            except (ValueError, TypeError) as e:
                logger.warning("respondent_parse_error", error=str(e))
        return surveys

    def _parse_html(self, html: str) -> List[Survey]:
        import json, re
        surveys = []
        # Respondent embeds data as JSON in script tags
        blobs = re.findall(r'<script[^>]+type="application/json"[^>]*>({.+?})</script>', html, re.DOTALL)
        for blob in blobs:
            try:
                data = json.loads(blob)
                for s in data.get("projects", [])[:20]:
                    sid = str(s.get("id", self._ts()))
                    surveys.append(Survey(
                        id=sid, title=s.get("title", "Untitled"),
                        payout=float(s.get("payout", 0)),
                        duration_minutes=int(s.get("duration", 0)),
                        source="respondent",
                        url=STUDY_URL.format(id=sid),
                    ))
            except Exception:
                pass
        return surveys

    @staticmethod
    def _ts() -> str:
        return str(int(datetime.now(timezone.utc).timestamp()))