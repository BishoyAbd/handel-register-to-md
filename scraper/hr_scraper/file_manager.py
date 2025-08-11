import pathlib
from . import config
from .logger import get_logger
from playwright.async_api import Download, Page

logger = get_logger(__name__)

class FileManager:
    def __init__(self, download_dir: str = config.DOWNLOADS_DIR):
        self.base_download_dir = pathlib.Path(download_dir)
        self.base_download_dir.mkdir(exist_ok=True)

    def get_safe_name(self, name_part: str) -> str:
        """Creates a filesystem-safe string from a name part."""
        s_name = "".join(c for c in name_part if c.isalnum() or c in (' ', '-', '_')).strip()
        return s_name.replace(' ', '_')

    def create_company_directory(self, company_name: str, reg_number: str) -> pathlib.Path:
        """Creates and returns a directory path for a specific company."""
        company_part = self.get_safe_name(company_name)
        dir_name = f"{company_part}_{reg_number}"
        company_dir = self.base_download_dir / dir_name
        company_dir.mkdir(exist_ok=True)
        logger.info(f"Using download directory: {company_dir}")
        return company_dir

    def get_document_filename(self, company_name: str, doc_type: str) -> str:
        """Creates a safe filename for a document."""
        company_part = self.get_safe_name(company_name)
        return f"{company_part}_{doc_type}.pdf"

    async def save_download(self, download: Download, full_path: pathlib.Path):
        await download.save_as(full_path)
        logger.info(f"Saved file: {full_path}")

    def save_markdown_content(self, markdown_content: str, full_path: pathlib.Path):
        """Saves the given markdown string to the specified path."""
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            logger.info(f"Saved markdown file: {full_path}")
        except Exception as e:
            logger.error(f"Failed to save markdown file {full_path}: {e}")

    async def save_debug_screenshot(self, page: Page, filename: str):
        try:
            path = self.base_download_dir / f"debug_{filename}.png"
            await page.screenshot(path=path)
            logger.info(f"Saved debug screenshot: {path}")
        except Exception as e:
            logger.warning(f"Could not save debug screenshot: {e}")

    async def save_debug_html(self, page: Page, filename: str):
        try:
            path = self.base_download_dir / f"debug_{filename}.html"
            content = await page.content()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Saved debug HTML: {path}")
        except Exception as e:
            logger.warning(f"Could not save debug HTML: {e}")
