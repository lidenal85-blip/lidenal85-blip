import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from survey_finder.logging.logger import init_logger

logger = init_logger()


class PlaywrightBrowser:
    """Singleton browser manager for Playwright."""

    _instance: Optional["PlaywrightBrowser"] = None
    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Initialize browser instance."""
        if self._browser:
            logger.info("browser_already_initialized")
            return

        logger.info("browser_initializing", headless=headless)

        self._playwright = await async_playwright().start()

        launch_options = {
            "headless": headless,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"]
        }

        if proxy:
            launch_options["proxy"] = {"server": proxy}

        self._browser = await self._playwright.chromium.launch(**launch_options)

        context_options = {
            "viewport": {"width": 1280, "height": 720},
            "user_agent": user_agent or self._default_user_agent()
        }

        self._context = await self._browser.new_context(**context_options)
        logger.info("browser_initialized")

    async def get_context(self) -> BrowserContext:
        """Get browser context."""
        if not self._context:
            raise RuntimeError("Browser not initialized")
        return self._context

    async def new_page(self) -> Page:
        """Create a new page."""
        context = await self.get_context()
        return await context.new_page()

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if hasattr(self, "_playwright"):
            await self._playwright.stop()

        logger.info("browser_closed")

    def _default_user_agent(self) -> str:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
