import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from survey_finder.adapters.base import BaseAdapter, AdapterConfig, AdapterResult
from survey_finder.adapters.http import HTTPClient
from survey_finder.adapters.nimble import NimbleClient
from survey_finder.hardening.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.cycle import CycleContext
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://www.prolific.com"
API_URL  = "https://www.prolific.com/api/v1"
STUDY_URL = "https://app.prolific.com/studies/{id}"


class ProlificAdapter(BaseAdapter):
    """Adapter for Prolific.co — API first, Nimble scrape as fallback."""

    def __init__(self, config: AdapterConfig) -> None:
        super().__init__(config)
        self.base_url = BASE_URL
        self.api_url  = API_URL
        self._nimble = NimbleClient()
        self._cb = CircuitBreaker(name="prolific", config=CircuitBreakerConfig(failure_threshold=3, timeout_seconds=120))

    async def initialize(self) -> None:
        logger.info("prolific_initializing")
        self._is_initialized = True

    async def fetch_surveys(self, context: CycleContext) -> AdapterResult:
        logger.info("prolific_fetch_start", cycle_id=context.cycle_id)
        surveys: List[Survey] = []
        errors:  List[Dict[str, Any]] = []

        # 1. Prolific public API
        try:
            api_surveys = await self._cb.async_call(self._fetch_via_api, context)
            surveys.extend(api_surveys)
            logger.info("prolific_api_ok", count=len(api_surveys))
        except Exception as e:
            logger.warning("prolific_api_failed", error=str(e))
            errors.append({"source": "prolific", "stage": "api", "error": str(e), "retryable": True})

        # 2. Nimble fallback when API yields nothing
        if not surveys and self._nimble.enabled:
            try:
                nimble_surveys = await self._fetch_via_nimble(context)
                surveys.extend(nimble_surveys)
                logger.info("prolific_nimble_ok", count=len(nimble_surveys))
            except Exception as e:
                logger.warning("prolific_nimble_failed", error=str(e))
                errors.append({"source": "prolific", "stage": "nimble", "error": str(e), "retryable": True})

        return AdapterResult(source="prolific", surveys=surveys, errors=errors, total_fetched=len(surveys))

    async def close(self) -> None:
        self._is_initialized = False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _fetch_via_api(self, context: CycleContext) -> List[Survey]:
        headers = {"Accept": "application/json",
                   "User-Agent": "Mozilla/5.0 (compatible; SurveyFinder/1.0)"}
        async with HTTPClient(timeout_seconds=self.config.timeout_seconds, headers=headers) as client:
            resp = await client.get(f"{API_URL}/studies/available")
            if resp.status_code == 200:
                return self._parse_api(resp.json())
            logger.warning("prolific_api_status", status=resp.status_code)
            return []

    async def _fetch_via_nimble(self, context: CycleContext) -> List[Survey]:
        """Scrape Prolific listing page through Nimble residential proxies."""
        html = await self._nimble.fetch_html(f"{BASE_URL}/studies", render_js=True)
        if not html:
            return []
        return self._parse_html(html)

    def _parse_api(self, data: Dict[str, Any]) -> List[Survey]:
        surveys = []
        for s in data.get("results", [])[:20]:
            try:
                sid = s.get("id", f"prolific_{self._ts()}")
                surveys.append(Survey(
                    id=sid,
                    title=s.get("name", "Untitled"),
                    payout=float(s.get("reward", 0)),
                    duration_minutes=int(s.get("estimated_completion_time", s.get("estimated_duration", 0))),
                    source="prolific",
                    url=STUDY_URL.format(id=sid),
                    description=s.get("description", ""),
                    places_available=s.get("places_taken", None) and
                                      s.get("total_available_places", 0) - s.get("places_taken", 0),
                    deadline=s.get("expiration", None),
                    device_requirements=s.get("device_compatibility", []),
                    country=s.get("filters", {}).get("country", None),
                    eligibility_criteria=s.get("filters", {}),
                ))
            except (ValueError, TypeError) as e:
                logger.warning("prolific_parse_error", error=str(e))
        return surveys

    def _parse_html(self, html: str) -> List[Survey]:
        """Best-effort parse of Prolific listing HTML."""
        surveys = []
        # Look for JSON-LD or data blobs embedded in the page
        import json, re
        blobs = re.findall(r'__NEXT_DATA__\s*=\s*({.+?})</script>', html, re.DOTALL)
        for blob in blobs:
            try:
                data = json.loads(blob)
                studies = (
                    data.get("props", {}).get("pageProps", {}).get("studies", []) or
                    data.get("props", {}).get("pageProps", {}).get("availableStudies", [])
                )
                for s in studies[:20]:
                    sid = str(s.get("id", self._ts()))
                    surveys.append(Survey(
                        id=sid, title=s.get("name", "Untitled"),
                        payout=float(s.get("reward", 0)),
                        duration_minutes=int(s.get("estimated_completion_time", 0)),
                        source="prolific",
                        url=STUDY_URL.format(id=sid),
                    ))
            except Exception:
                pass
        return surveys

    @staticmethod
    def _ts() -> str:
        return str(int(datetime.now(timezone.utc).timestamp()))

    @staticmethod
    def _parse_float(text: Optional[str]) -> float:
        if not text:
            return 0.0
        m = re.search(r"[\d.]+", text)
        return float(m.group()) if m else 0.0

    @staticmethod
    def _parse_int(text: Optional[str]) -> int:
        if not text:
            return 0
        m = re.search(r"\d+", text)
        return int(m.group()) if m else 0