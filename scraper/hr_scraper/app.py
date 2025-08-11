import re
from typing import Optional
from .browser_manager import BrowserManager
from .navigator import Navigator
from .data_extractor import DataExtractor
from .company_matcher import CompanyMatcher
from .file_manager import FileManager
from .pdf_extractor import PDFExtractor
from .logger import get_logger
from .exceptions import ScraperException, CompanyNotFoundError

logger = get_logger(__name__)

class ScraperApp:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.file_manager = FileManager()
        self.company_matcher = CompanyMatcher()
        self.pdf_extractor = PDFExtractor()

    async def run(self, company_name: str, registration_number: Optional[str] = None) -> dict:
        logger.info(f"Starting scraper for: '{company_name}'")
        extracted_markdowns = {}
        try:
            async with BrowserManager(headless=self.headless) as page:
                navigator = Navigator(page)
                extractor = DataExtractor(page)

                await navigator.go_to_homepage()
                await navigator.go_to_search_page()

                # Use the company name for the search, not the HRB number
                await navigator.perform_search(company_name)

                companies = await extractor.extract_companies()
                if not companies:
                    raise CompanyNotFoundError("No companies found on the results page.")

                hrb_match = re.search(r'HRB\s*(\d+)', company_name, re.IGNORECASE)
                target_hrb = registration_number or (hrb_match.group(1) if hrb_match else None)
                best_match = self.company_matcher.find_best_match(company_name, companies, target_hrb)
                if not best_match:
                    raise CompanyNotFoundError("No suitable company match found.")

                # Ensure we have a registration number for the directory name
                if not best_match.hrb:
                    logger.error(f"Cannot create directory for '{best_match.name}' without a registration number.")
                    return {}

                documents = await extractor.extract_documents_for_company(best_match)
                if not documents:
                    logger.warning(f"No documents found for '{best_match.name}'.")
                    # Original logic: save debug files and check for messages
                    await self.file_manager.save_debug_screenshot(page, "no_docs")
                    await self.file_manager.save_debug_html(page, "no_docs")
                    await extractor.get_ui_messages()
                    return {}

                # Use the original company name for the directory and filenames
                company_dir = self.file_manager.create_company_directory(company_name, best_match.hrb)

                downloaded_count = 0
                for doc in documents:
                    try:
                        download = await navigator.download_document(doc.link_id)
                        pdf_filename = self.file_manager.get_document_filename(company_name, doc.doc_type)
                        pdf_path = company_dir / pdf_filename
                        await self.file_manager.save_download(download, pdf_path)
                        downloaded_count += 1

                        # Phase 2: Extract content from the downloaded PDF
                        markdown_content = self.pdf_extractor.extract_content_as_markdown(pdf_path)
                        
                        # Save the markdown content to a file
                        md_filename = pdf_path.with_suffix('.md').name
                        md_path = company_dir / md_filename
                        self.file_manager.save_markdown_content(markdown_content, md_path)
                        
                        # Store in memory to return to the client
                        extracted_markdowns[doc.doc_type] = markdown_content
                        
                    except ScraperException as e:
                        logger.error(f"Failed to download or process document: {e}")

                logger.info(f"Successfully downloaded and processed {downloaded_count} documents for '{company_name}'.")

        except ScraperException as e:
            logger.error(f"A scraper-related error occurred: {e}")
        except Exception as e:
            logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
            # Original logic: save a final error screenshot
            if 'page' in locals():
                await self.file_manager.save_debug_screenshot(page, "error_working")
        
        return extracted_markdowns
