from playwright.async_api import Page, Download
from . import config
from .logger import get_logger
from .exceptions import NavigationError, DownloadFailedError

logger = get_logger(__name__)

class Navigator:
    def __init__(self, page: Page):
        self.page = page

    async def go_to_homepage(self):
        logger.info(f"Navigating to homepage: {config.HOME_URL}")
        try:
            await self.page.goto(config.HOME_URL, wait_until="domcontentloaded", timeout=config.DEFAULT_TIMEOUT)
            # Try to accept cookies if dialog appears to avoid UI blocking
            try:
                cookie_btn = self.page.get_by_role("button", name=r".*(Akzeptieren|Accept|Zustimmen).*", exact=False)
                await cookie_btn.wait_for(timeout=2500)
                await cookie_btn.click()
            except Exception:
                pass
            await self.page.wait_for_timeout(2000)
        except Exception as e:
            # Replicate original logic: log a warning and continue
            logger.warning(f"Homepage load issue, continuing anyway: {e}")

    async def go_to_search_page(self):
        logger.info("Navigating to search page...")
        try:
            nav_link = self.page.locator(config.SEARCH_PAGE_LINK)
            await nav_link.wait_for(timeout=config.NAVIGATION_TIMEOUT)
            await nav_link.click()
            await self.page.wait_for_timeout(3000)
        except Exception as e:
            raise NavigationError(f"Failed to navigate to search page: {e}")

    async def perform_search(self, search_query: str):
        logger.info(f"Performing search for: {search_query}")
        try:
            search_field = self.page.locator(config.SEARCH_INPUT)
            await search_field.wait_for(timeout=config.NAVIGATION_TIMEOUT)
            await search_field.clear()
            await search_field.fill(search_query)

            search_button = self.page.locator(config.SEARCH_BUTTON)
            await search_button.wait_for(timeout=config.NAVIGATION_TIMEOUT)
            await search_button.click()
            # Wait for the results form and its rows to appear to avoid racing Ajax updates
            try:
                results_form = self.page.locator(config.RESULTS_FORM_SELECTOR)
                await results_form.wait_for(timeout=config.RESULTS_TIMEOUT)
                await self.page.locator(config.RESULTS_TABLE_ROW_SELECTOR).first.wait_for(timeout=config.RESULTS_TIMEOUT)
                await self.page.wait_for_load_state('networkidle')
            except Exception:
                # Fallback small delay
                await self.page.wait_for_timeout(4000)
        except Exception as e:
            raise NavigationError(f"Search failed: {e}")

    async def download_document(self, link_id: str) -> Download:
        logger.info(f"Downloading document with link ID: {link_id}")
        try:
            link_element = self.page.locator(f'a[id="{link_id}"]')
            await link_element.scroll_into_view_if_needed()
            async with self.page.expect_download(timeout=config.DOWNLOAD_TIMEOUT) as download_info:
                await link_element.click()
                await self.page.wait_for_timeout(1000)
            return await download_info.value
        except Exception as e:
            raise DownloadFailedError(f"Download failed for link ID {link_id}: {e}")
