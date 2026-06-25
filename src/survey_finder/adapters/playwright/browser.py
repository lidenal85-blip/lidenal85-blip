import asyncio
from typing import Optional

from survey_finder.logging.logger import init_logger
from survey_finder.adapters.playwright import HAVE_PLAYWRIGHT

logger = init_logger()


class PlaywrightBrowser:
    """Singleton browser manager for Playwright."""
    
    _instance: Optional["PlaywrightBrowser"] = None
    _browser = None
    _context = None
    _playwright = None

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
        if not HAVE_PLAYWRIGHT:
            logger.warning("playwright_not_installed", 
                          message="Install: pip install playwright && playwright install chromium")
            return

        if self._browser:
            logger.info("browser_already_initialized")
            return

        logger.info("browser_initializing", headless=headless)
        
        try:
            from playwright.async_api import async_playwright
            
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
            
        except Exception as e:
            logger.error("browser_init_failed", error=str(e))
            raise

    async def get_context(self):
        """Get browser context."""
        if not HAVE_PLAYWRIGHT:
            raise RuntimeError("Playwright not installed")
        if not self._context:
            raise RuntimeError("Browser not initialized")
        return self._context

    async def new_page(self):
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
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        logger.info("browser_closed")

    def _default_user_agent(self) -> str:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
