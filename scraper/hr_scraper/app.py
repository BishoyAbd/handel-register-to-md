import re
from typing import Optional, Dict, List, Tuple, Union
from .browser_manager import BrowserManager
from .navigator import Navigator
from .data_extractor import DataExtractor
from .company_matcher import CompanyMatcher
from .file_manager import FileManager
from .pdf_extractor import PDFExtractor
from .logger import get_logger
from .exceptions import ScraperException, CompanyNotFoundError
from .models import DocumentType

logger = get_logger(__name__)

class ScraperApp:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.file_manager = FileManager()
        self.company_matcher = CompanyMatcher()
        self.pdf_extractor = PDFExtractor()

    async def run(self, company_name: str, registration_number: Optional[str] = None, 
                  document_types: Optional[List[DocumentType]] = None) -> Dict[str, Union[str, bytes, Dict]]:
        """
        Run the scraper and return extracted data.
        
        Args:
            company_name: Name of the company to search for
            registration_number: Optional registration number (HRB)
            document_types: Optional list of document types to download (AD, CD, or both)
                           If None, downloads all available documents
        
        Returns:
            Dict containing:
            - 'success': bool indicating if scraping was successful
            - 'error': str error message if failed, None if successful
            - 'retry_recommended': bool indicating if retry is recommended
            - 'company_info': dict with company details
            - 'documents': list of dicts with document data (PDF bytes and markdown)
            - 'debug_info': dict with debug information for troubleshooting
        """
        logger.info(f"Starting scraper for: '{company_name}' with document types: {[dt.value for dt in document_types] if document_types else 'all'}")
        
        result = {
            'success': False,
            'error': None,
            'retry_recommended': False,
            'company_info': None,
            'documents': [],
            'debug_info': {}
        }
        
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
                    result['error'] = "No companies found on the results page."
                    result['retry_recommended'] = True
                    return result

                hrb_match = re.search(r'HRB\s*(\d+)', company_name, re.IGNORECASE)
                target_hrb = registration_number or (hrb_match.group(1) if hrb_match else None)
                best_match = self.company_matcher.find_best_match(company_name, companies, target_hrb)
                if not best_match:
                    result['error'] = "No suitable company match found."
                    result['retry_recommended'] = True
                    return result

                # Store company info
                result['company_info'] = {
                    'name': best_match.name,
                    'hrb': best_match.hrb,
                    'search_query': company_name
                }

                # Ensure we have a registration number
                if not best_match.hrb:
                    result['error'] = f"Cannot process company '{best_match.name}' without a registration number."
                    result['retry_recommended'] = False
                    return result

                # Extract documents with optional filtering
                documents = await extractor.extract_documents_for_company(best_match, document_types)
                if not documents:
                    result['error'] = f"No documents found for '{best_match.name}' with requested types: {[dt.value for dt in document_types] if document_types else 'all'}"
                    result['retry_recommended'] = True
                    # Save debug info for troubleshooting
                    await self.file_manager.save_debug_screenshot(page, "no_docs")
                    await self.file_manager.save_debug_html(page, "no_docs")
                    ui_messages = await extractor.get_ui_messages()
                    result['debug_info'] = {
                        'screenshot_saved': True,
                        'html_saved': True,
                        'ui_messages': ui_messages
                    }
                    return result

                # Process each document
                for doc in documents:
                    try:
                        # Download document
                        download = await navigator.download_document(doc.link_id)
                        
                        # Create a temporary file for the download (needed for Playwright)
                        import tempfile
                        import os
                        temp_pdf_path = tempfile.mktemp(suffix='.pdf')
                        
                        try:
                            # Save the download to the temporary file (Playwright requirement)
                            await download.save_as(temp_pdf_path)
                            
                            # Read the PDF content as bytes
                            with open(temp_pdf_path, 'rb') as f:
                                pdf_content = f.read()
                            
                            # Extract markdown content from the PDF bytes (in-memory)
                            markdown_content = self.pdf_extractor.extract_content_from_bytes(
                                pdf_content, 
                                f"{best_match.name}_{doc.doc_type.value}.pdf"
                            )
                            
                            # Store document data - CLIENT GETS THIS!
                            document_data = {
                                'doc_type': doc.doc_type.value,
                                'pdf_content': pdf_content,           # PDF as bytes for client
                                'pdf_filename': f"{best_match.name}_{doc.doc_type.value}.pdf",
                                'markdown_content': markdown_content, # Markdown as string for client
                                'markdown_filename': f"{best_match.name}_{doc.doc_type.value}.md"
                            }
                            result['documents'].append(document_data)
                            
                            logger.info(f"Successfully processed document {doc.doc_type.value}: {len(pdf_content)} bytes")
                            
                        finally:
                            # Clean up temporary file
                            try:
                                if os.path.exists(temp_pdf_path):
                                    os.unlink(temp_pdf_path)
                            except:
                                pass
                        
                    except ScraperException as e:
                        logger.error(f"Failed to download or process document: {e}")
                        result['debug_info']['document_errors'] = result['debug_info'].get('document_errors', [])
                        result['debug_info']['document_errors'].append({
                            'doc_type': doc.doc_type.value,
                            'error': str(e)
                        })

                # Mark as successful if we have at least one document
                if result['documents']:
                    result['success'] = True
                    logger.info(f"Successfully processed {len(result['documents'])} documents for '{company_name}'.")
                else:
                    result['error'] = "Failed to process any documents."
                    result['retry_recommended'] = True

        except ScraperException as e:
            logger.error(f"A scraper-related error occurred: {e}")
            result['error'] = f"Scraper error: {str(e)}"
            result['retry_recommended'] = True
        except Exception as e:
            logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
            result['error'] = f"Unexpected error: {str(e)}"
            result['retry_recommended'] = True
            # Save debug info for unexpected errors
            if 'page' in locals():
                await self.file_manager.save_debug_screenshot(page, "error_working")
                result['debug_info']['error_screenshot_saved'] = True
        
        return result
