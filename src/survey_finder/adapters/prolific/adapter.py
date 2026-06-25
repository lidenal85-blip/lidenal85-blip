import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from playwright.async_api import Page

from survey_finder.adapters.base import BaseAdapter, AdapterConfig, AdapterResult
from survey_finder.adapters.playwright.context import browser_page
from survey_finder.adapters.http import HTTPClient
from survey_finder.adapters.session import SessionManager
from survey_finder.adapters.errors import AdapterError, AdapterErrorType
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.cycle import CycleContext
from survey_finder.logging.logger import init_logger

logger = init_logger()


class ProlificAdapter(BaseAdapter):
    """Adapter for Prolific.co survey platform."""

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.session_manager = SessionManager()
        self.base_url = "https://www.prolific.com"
        self.api_url = "https://www.prolific.com/api/v1"

    async def initialize(self) -> None:
        """Initialize Prolific adapter."""
        logger.info("prolific_initializing")

        # Check for existing session
        session = self.session_manager.get_session("prolific")
        if session and self.session_manager.is_valid("prolific"):
            logger.info("prolific_session_restored")
            self._is_initialized = True
            return

        logger.info("prolific_no_session")
        self._is_initialized = True

    async def fetch_surveys(self, context: CycleContext) -> AdapterResult:
        """Fetch available surveys from Prolific."""
        logger.info("prolific_fetch_start", cycle_id=context.cycle_id)

        surveys: List[Survey] = []
        errors: List[Dict[str, Any]] = []

        try:
            # Try API first
            api_surveys = await self._fetch_via_api(context)
            if api_surveys:
                surveys.extend(api_surveys)
                logger.info("prolific_api_success", count=len(api_surveys))

            # If API fails or returns few results, try browser
            if len(surveys) < 5:
                browser_surveys = await self._fetch_via_browser(context)
                surveys.extend(browser_surveys)
                logger.info("prolific_browser_success", count=len(browser_surveys))

        except Exception as e:
            logger.error("prolific_fetch_failed", error=str(e))
            errors.append({
                "source": "prolific",
                "error": str(e),
                "retryable": True
            })

        return AdapterResult(
            source="prolific",
            surveys=surveys,
            errors=errors,
            total_fetched=len(surveys)
        )

    async def close(self) -> None:
        """Close adapter resources."""
        logger.info("prolific_closing")
        self._is_initialized = False

    async def _fetch_via_api(self, context: CycleContext) -> List[Survey]:
        """Fetch surveys via Prolific API."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with HTTPClient(
            timeout_seconds=self.config.timeout_seconds,
            headers=headers
        ) as client:

            try:
                response = await client.get(
                    f"{self.api_url}/studies/available"
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_api_response(data)

                elif response.status_code == 401:
                    # Need to login via browser
                    return []

                else:
                    logger.warning("prolific_api_error", status=response.status_code)
                    return []

            except Exception as e:
                logger.warning("prolific_api_failed", error=str(e))
                return []

    async def _fetch_via_browser(self, context: CycleContext) -> List[Survey]:
        """Fetch surveys via browser automation."""
        surveys: List[Survey] = []

        try:
            async with browser_page(
                headless=True,
                user_agent=self._default_user_agent()
            ) as page:

                # Navigate to Prolific
                await page.goto(f"{self.base_url}/studies", wait_until="networkidle")

                # Check if logged in
                if await page.locator("text=Login").count() > 0:
                    logger.warning("prolific_login_required")
                    return []

                # Wait for studies to load
                await page.wait_for_selector("[data-testid='study-card']", timeout=30000)

                # Extract study data
                study_cards = await page.locator("[data-testid='study-card']").all()

                for card in study_cards[:10]:  # Limit to 10
                    try:
                        title = await card.locator("[data-testid='study-title']").text_content() or "Untitled"
                        reward = await card.locator("[data-testid='study-reward']").text_content()
                        duration = await card.locator("[data-testid='study-duration']").text_content()

                        survey = Survey(
                            id=f"prolific_{datetime.utcnow().timestamp()}",
                            title=title.strip(),
                            payout=self._parse_reward(reward),
                            duration_minutes=self._parse_duration(duration),
                            source="prolific"
                        )
                        surveys.append(survey)

                    except Exception as e:
                        logger.warning("prolific_parse_error", error=str(e))
                        continue

        except Exception as e:
            logger.error("prolific_browser_failed", error=str(e))
            raise

        return surveys

    def _parse_api_response(self, data: Dict[str, Any]) -> List[Survey]:
        """Parse Prolific API response."""
        surveys: List[Survey] = []

        studies = data.get("results", [])
        for study in studies[:10]:
            try:
                survey = Survey(
                    id=study.get("id", f"prolific_{datetime.utcnow().timestamp()}"),
                    title=study.get("name", "Untitled"),
                    payout=float(study.get("reward", 0)),
                    duration_minutes=int(study.get("estimated_duration", 0)),
                    source="prolific"
                )
                surveys.append(survey)
            except (ValueError, TypeError) as e:
                logger.warning("prolific_parse_error", error=str(e))
                continue

        return surveys

    def _parse_reward(self, text: Optional[str]) -> float:
        """Parse reward string to float."""
        if not text:
            return 0.0
        try:
            # Extract number from text like "£5.00" or "$10.00"
            import re
            match = re.search(r"[\d.]+", text)
            if match:
                return float(match.group())
        except Exception:
            pass
        return 0.0

    def _parse_duration(self, text: Optional[str]) -> int:
        """Parse duration string to minutes."""
        if not text:
            return 0
        try:
            import re
            match = re.search(r"\d+", text)
            if match:
                return int(match.group())
        except Exception:
            pass
        return 0

    def _default_user_agent(self) -> str:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
