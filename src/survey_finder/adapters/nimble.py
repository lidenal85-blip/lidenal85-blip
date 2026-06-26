"""
Nimble Web API client — residential proxy scraping without local browser.
Docs: https://docs.nimbleway.com/nimble-api/web-api
"""
from typing import Optional
import httpx
from survey_finder.config.settings import settings
from survey_finder.logging.logger import init_logger

logger = init_logger()

TIMEOUT = 30.0


class NimbleClient:
    """
    Thin async wrapper around Nimble Web API.
    Falls back gracefully when NIMBLE_API_KEY is not set.
    """

    def __init__(self) -> None:
        self._api_key = settings.NIMBLE_API_KEY
        self._url = settings.NIMBLE_API_URL
        self._enabled = bool(self._api_key)
        if not self._enabled:
            logger.warning("nimble_disabled", reason="NIMBLE_API_KEY not set")

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def fetch_html(
        self,
        url: str,
        render_js: bool = True,
        country: str = "US",
    ) -> Optional[str]:
        """
        Fetch a page through Nimble residential proxies.
        Returns HTML string or None on failure.
        """
        if not self._enabled:
            logger.warning("nimble_skip", url=url, reason="no_api_key")
            return None

        payload = {
            "url": url,
            "render": render_js,
            "country": country,
            "method": "GET",
        }

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(
                    self._url,
                    json=payload,
                    auth=(self._api_key, ""),  # Nimble uses Basic auth
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                html = data.get("html_content") or data.get("content", "")
                logger.info("nimble_ok", url=url, size=len(html))
                return html

        except httpx.HTTPStatusError as e:
            logger.error("nimble_http_error", url=url, status=e.response.status_code)
            return None
        except Exception as e:
            logger.error("nimble_error", url=url, error=str(e))
            return None

    async def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> list[dict]:
        """
        SERP search via Nimble.
        Returns list of {title, url, snippet}.
        """
        if not self._enabled:
            return []

        payload = {
            "query": query,
            "search_engine": "google_search",
            "num_results": num_results,
        }

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(
                    "https://api.nimbleway.com/v1/serp",
                    json=payload,
                    auth=(self._api_key, ""),
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            logger.error("nimble_serp_error", query=query, error=str(e))
            return []