from playwright.async_api import async_playwright, Browser, Page
from . import config
from .logger import get_logger

logger = get_logger(__name__)

class BrowserManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    async def __aenter__(self) -> Page:
        logger.info("Launching browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(config.DEFAULT_TIMEOUT)
        await self.page.set_extra_http_headers({'User-Agent': config.USER_AGENT})
        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed.")
