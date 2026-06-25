"""
Playwright adapter for browser automation.
Requires: playwright package and chromium installation.
"""

try:
    from playwright.async_api import Page, BrowserContext
    HAVE_PLAYWRIGHT = True
except ImportError:
    HAVE_PLAYWRIGHT = False
    
    # Stub classes for when Playwright is not installed
    class Page: pass
    class BrowserContext: pass
