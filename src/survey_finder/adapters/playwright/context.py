from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from survey_finder.adapters.playwright import HAVE_PLAYWRIGHT
from survey_finder.adapters.playwright.browser import PlaywrightBrowser
from survey_finder.logging.logger import init_logger

logger = init_logger()


@asynccontextmanager
async def browser_page(
    headless: bool = True,
    proxy: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AsyncGenerator:
    """Context manager for browser page."""
    if not HAVE_PLAYWRIGHT:
        logger.warning("playwright_not_installed_browser_page")
        yield None
        return
    
    browser = PlaywrightBrowser()
    
    try:
        await browser.initialize(headless=headless, proxy=proxy, user_agent=user_agent)
        page = await browser.new_page()
        page.set_default_timeout(30000)
        logger.debug("browser_page_created")
        yield page
    finally:
        await page.close()
        await browser.close()
