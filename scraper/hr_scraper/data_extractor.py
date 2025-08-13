from playwright.async_api import Page
from typing import List, Dict, Any, Optional
from .models import Company, Document, DocumentType
from .logger import get_logger

logger = get_logger(__name__)

class DataExtractor:
    def __init__(self, page: Page):
        self.page = page

    async def extract_companies(self) -> List[Company]:
        logger.info("Extracting companies from the page...")
        company_data = await self.page.evaluate("""
            () => {
                const companies = [];
                const tableRows = document.querySelectorAll('tr');
                
                tableRows.forEach(row => {
                    const links = row.querySelectorAll('a[id*="j_idt"]');
                    let hasAdOrCd = false;
                    links.forEach(link => {
                        const text = link.textContent.trim();
                        if (text === 'AD' || text === 'CD') {
                            hasAdOrCd = true;
                        }
                    });
                    
                    if (hasAdOrCd) {
                        let companyName = null;
                        let registrationNumber = null;
                        
                        const cells = row.querySelectorAll('td');
                        if (cells.length > 0) {
                            for (let i = 0; i < cells.length; i++) {
                                const cell = cells[i];
                                const text = cell.textContent.trim();
                                
                                if (text && text.includes('HRB') && /HRB\s*\d+/.test(text)) {
                                    const hrbMatch = text.match(/HRB\s*(\d+)/);
                                    if (hrbMatch) {
                                        registrationNumber = hrbMatch[1];
                                    }
                                }
                                
                                if (text && 
                                    text.length > 5 &&
                                    /[a-zA-Z]/.test(text) &&
                                    !text.includes('1.)') && 
                                    !text.includes('2.)') && 
                                    !text.includes('3.)') && 
                                    !text.includes('Historie') &&
                                    !text.includes('AD') &&
                                    !text.includes('CD') &&
                                    !/HRB\s*\d+/.test(text)
                                ) {
                                    const cleanText = text.replace(/\s+/g, ' ').trim();
                                    if (cleanText.length > 5) {
                                        companyName = cleanText;
                                    }
                                }
                            }
                            
                            if (companyName) {
                                companies.push({
                                    name: companyName,
                                    hrb: registrationNumber
                                });
                            }
                        }
                    }
                });
                return companies;
            }
        """)
        
        companies = [Company(name=c['name'], hrb=c['hrb']) for c in company_data]
        logger.info(f"Found {len(companies)} companies.")
        return companies

    async def extract_documents_for_company(self, company: Company, document_types: Optional[List[DocumentType]] = None) -> List[Document]:
        """
        Extract documents for a company, optionally filtered by document types.
        
        Args:
            company: The company to extract documents for
            document_types: Optional list of document types to filter by (AD, CD, or both)
        """
        logger.info(f"Extracting documents for {company.name} (HRB: {company.hrb})...")
        if not company.hrb:
            return []

        # If no document types specified, get all available
        if document_types is None:
            document_types = [DocumentType.AD, DocumentType.CD]
        
        # Convert enum values to strings for comparison
        requested_types = [dt.value for dt in document_types]
        logger.info(f"Requested document types: {requested_types}")

        company_docs = await self.page.evaluate("""
            (args) => {
                const registrationNumber = args.registrationNumber;
                const requestedTypes = args.requestedTypes;
                const docs = [];
                const tableRows = document.querySelectorAll('tr');
                
                tableRows.forEach(row => {
                    const rowText = row.textContent;
                    if (registrationNumber && rowText.includes('HRB ' + registrationNumber)) {
                        const links = row.querySelectorAll('a[id*="j_idt"]');
                        links.forEach(link => {
                            const text = link.textContent.trim();
                            if (requestedTypes.includes(text)) {
                                docs.push({
                                    id: link.id,
                                    text: text,
                                    href: link.href
                                });
                            }
                        });
                    }
                });
                return docs;
            }
        """, {"registrationNumber": company.hrb, "requestedTypes": requested_types})

        documents = [
            Document(
                id=doc['id'], 
                text=doc['text'], 
                doc_type=DocumentType(doc['text']), 
                company_name=company.name, 
                link_id=doc['id']
            ) 
            for doc in company_docs
        ]
        logger.info(f"Found {len(documents)} documents for {company.name}.")
        return documents

    async def get_ui_messages(self) -> List[str]:
        logger.info("Checking for UI messages on page...")
        messages = await self.page.evaluate("""
            (selectors) => {
                let messages = [];
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        if (el.textContent.trim()) {
                            messages.push(el.textContent.trim());
                        }
                    });
                });
                return messages;
            }
        """, config.ERROR_MESSAGE_SELECTORS)
        if messages:
            logger.info(f"Found UI messages: {messages}")
        return messages
