from playwright.async_api import Page
from typing import List, Dict, Any, Optional
from .models import Company, Document, DocumentType
from .logger import get_logger

logger = get_logger(__name__)

class DataExtractor:
    def __init__(self, page: Page):
        self.page = page

    async def extract_companies(self, search_query: Optional[str] = None) -> List[Company]:
        logger.info("Extracting companies from the page...")
        search_words = []
        if search_query:
            # Basic tokenization; scoring happens in the browser
            search_words = [w.lower() for w in search_query.split() if len(w) > 1]
        
        company_data = await self.page.evaluate(r"""
            (searchWords) => {
                const companies = [];
                const tableRows = Array.from(document.querySelectorAll('tr'));

                const clean = (txt) => (txt || '').replace(/\s+/g, ' ').trim();
                const isCandidateText = (txt) => {
                    if (!txt) return false;
                    const t = txt.toLowerCase();
                    if (t.length < 5) return false;
                    if (!/[a-zA-Z]/.test(t)) return false;
                    if (t.includes('historie')) return false;
                    if (t.includes('ad') && t.trim() === 'ad') return false;
                    if (t.includes('cd') && t.trim() === 'cd') return false;
                    if (/hrb\s*\d+/.test(t)) return false;
                    return true;
                };

                const scoreCandidate = (txt, words) => {
                    if (!words || words.length === 0) return 0;
                    const t = txt.toLowerCase();
                    let score = 0;
                    for (const w of words) {
                        if (t.includes(w)) score += 1;
                    }
                    return score;
                };

                for (const row of tableRows) {
                    const rowText = clean(row.textContent);
                    
                    // Check for documents (AD/CD/HD/DK/UT/VÖ/SI links and indicators)
                    const hasDocs = Array.from(row.querySelectorAll('a[id*="j_idt"], span.dokumentList')).some(el => {
                        const txt = clean(el.textContent).toUpperCase();
                        return ['AD', 'CD', 'HD', 'DK', 'UT', 'VÖ', 'SI'].includes(txt);
                    });

                    // Check for registration number (ALL German formats: HRB, HRA, PR, GnR, VR, GüR, EWIV, SE, SCE, SPE, etc.)
                    const allPrefixes = ['HRB', 'HRA', 'PR', 'GNR', 'VR', 'GÜR', 'EWIV', 'SE', 'SCE', 'SPE'];
                    const prefixPattern = allPrefixes.join('|');
                    const registrationMatch = rowText.match(new RegExp(`(${prefixPattern})\\s*(\\d+)`, 'i'));
                    const registrationNumber = registrationMatch ? registrationMatch[1] + ' ' + registrationMatch[2] : null;

                    // More flexible: accept rows that have either documents OR HRB OR look like company data
                    const hasCompanyData = rowText.length > 20 && 
                                         /[a-zA-Z]{3,}/.test(rowText) && 
                                         !rowText.includes('Historie') &&
                                         !rowText.includes('Zurück');

                    if (!hasDocs && !registrationNumber && !hasCompanyData) {
                        continue;
                    }

                    // Gather candidate name texts from likely elements
                    const candidateElements = [
                        ...row.querySelectorAll('strong, b, h1, h2, h3, h4, h5, h6, small, span, div, td')
                    ];
                    const seen = new Set();
                    const candidates = [];
                    
                    for (const el of candidateElements) {
                        const txt = clean(el.textContent);
                        if (!txt || seen.has(txt)) continue;
                        seen.add(txt);
                        if (isCandidateText(txt)) {
                            candidates.push(txt);
                        }
                    }

                    if (candidates.length === 0) {
                        // Fallback: split row text and look for meaningful segments
                        const parts = rowText.split(/\s{2,}|\n|\r/).map(clean).filter(isCandidateText);
                        candidates.push(...parts);
                    }

                    if (candidates.length === 0) continue;

                    // Choose best candidate by search word overlap, then by length
                    candidates.sort((a, b) => {
                        const sa = scoreCandidate(a, searchWords);
                        const sb = scoreCandidate(b, searchWords);
                        if (sa !== sb) return sb - sa;
                        return b.length - a.length;
                    });

                    const companyName = candidates[0];
                    if (companyName) {
                        companies.push({ 
                            name: companyName, 
                            hrb: registrationNumber,
                            hasDocs: hasDocs,
                            rowText: rowText.substring(0, 100) // Debug info
                        });
                    }
                }
                return companies;
            }
        """, search_words)
        
        companies = [Company(name=c['name'], hrb=c['hrb']) for c in company_data]
        logger.info(f"Found {len(companies)} companies.")
        
        # Log debug info for troubleshooting
        if company_data:
            for i, c in enumerate(company_data):
                logger.debug(f"Company {i+1}: '{c['name']}' (HRB: {c['hrb']}, HasDocs: {c['hasDocs']})")
                if c.get('rowText'):
                    logger.debug(f"  Row preview: {c['rowText']}...")
        
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

        company_docs = await self.page.evaluate(r"""
            (args) => {
                const registrationNumber = args.registrationNumber;
                const requestedTypes = args.requestedTypes;
                const docs = [];
                
                // Look for the company row that matches the registration number
                const tableRows = document.querySelectorAll('tr');
                
                tableRows.forEach(row => {
                    const rowText = row.textContent;
                    if (registrationNumber && rowText.includes(registrationNumber)) {
                        // Find document links in this row
                        const links = row.querySelectorAll('a[id*="j_idt"]');
                        links.forEach(link => {
                            const text = (link.textContent || '').trim();
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
        messages = await self.page.evaluate(r"""
            (selectors) => {
                let messages = [];
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        if (el.textContent && el.textContent.trim()) {
                            messages.push(el.textContent.trim());
                        }
                    });
                });
                return messages;
            }
        """, [])
        if messages:
            logger.info(f"Found UI messages: {messages}")
        return messages
