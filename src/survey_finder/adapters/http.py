import asyncio
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
import time

from survey_finder.adapters.errors import AdapterError, AdapterErrorType
from survey_finder.logging.logger import init_logger

logger = init_logger()


class HTTPClient:
    """HTTP client with retry and timeout support."""

    def __init__(
        self,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        retry_delay_seconds: int = 5,
        proxy: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.proxy = proxy
        self.headers = headers or {}
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def initialize(self) -> None:
        transport = None
        if self.proxy:
            transport = httpx.AsyncHTTPTransport(proxy=self.proxy)

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds),
            transport=transport,
            headers=self.headers
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        if not self._client:
            raise RuntimeError("HTTPClient not initialized")

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt < self.max_retries:
            try:
                logger.debug("http_request", method=method, url=url, attempt=attempt + 1)
                response = await self._client.request(method, url, **kwargs)

                if response.status_code == 429:
                    # Rate limit - retry after
                    retry_after = response.headers.get("Retry-After", "5")
                    try:
                        delay = int(retry_after)
                    except ValueError:
                        delay = 5
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue

                if response.status_code >= 500:
                    # Server error - retry
                    await asyncio.sleep(self.retry_delay_seconds)
                    attempt += 1
                    continue

                if response.status_code >= 400:
                    raise AdapterError(
                        error_type=AdapterErrorType.NETWORK,
                        message=f"HTTP {response.status_code}: {response.text[:200]}",
                        retryable=response.status_code >= 500
                    )

                return response

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning("http_timeout", url=url, attempt=attempt + 1)
                await asyncio.sleep(self.retry_delay_seconds)
                attempt += 1

            except AdapterError:
                raise

            except Exception as e:
                last_error = e
                logger.error("http_error", url=url, error=str(e), attempt=attempt + 1)
                await asyncio.sleep(self.retry_delay_seconds)
                attempt += 1

        raise AdapterError(
            error_type=AdapterErrorType.NETWORK,
            message=f"Failed after {self.max_retries} retries",
            retryable=True,
            cause=last_error
        )

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)
