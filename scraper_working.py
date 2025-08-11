import sys
import asyncio
from playwright.async_api import async_playwright
import pathlib
import time

HOME_URL = "https://www.handelsregister.de/"

async def search_and_download(company_name: str, registration_number: str = None):
    """
    Working scraper using ACTUAL element names and document link patterns
    
    Args:
        company_name: The company name to search for
        registration_number: Optional registration number (HRB, HRA, etc.) for more accurate matching
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set page timeout to prevent hanging
        page.set_default_timeout(30000)
        
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        try:
            print("🚀 Starting search with working method...")
            
            # Go to homepage with strict timeout
            print("1. Loading homepage...")
            try:
                await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"   ⚠️  Homepage load issue: {e}")
                # Continue anyway
            
            # Click the navigation link
            print("2. Navigating to search page...")
            try:
                nav_link = page.locator('#naviForm\\:normaleSucheLink')
                await nav_link.wait_for(timeout=10000)
                await nav_link.click()
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"   ❌ Navigation failed: {e}")
                return
            
            # Extract HRB number from search query if present
            import re
            hrb_match = re.search(r'HRB\s*(\d+)', company_name, re.IGNORECASE)
            target_hrb = hrb_match.group(1) if hrb_match else None
            company_name_clean = re.sub(r'HRB\s*\d+', '', company_name, flags=re.IGNORECASE).strip()
            
            if target_hrb:
                print(f"   🔢 Found HRB number in search: {target_hrb}")
                print(f"   🏢 Clean company name: {company_name_clean}")
                # Try HRB search first
                search_query = f"HRB {target_hrb}"
            else:
                print(f"   🔍 No HRB number found, using company name search")
                search_query = company_name
            
            # Fill search form
            print("3. Filling search form...")
            try:
                search_field = page.locator('#form\\:schlagwoerter')
                await search_field.wait_for(timeout=10000)
                await search_field.clear()
                await search_field.fill(search_query)
            except Exception as e:
                print(f"   ❌ Search field not found: {e}")
                return
            
            # Click search button
            print("4. Performing search...")
            try:
                search_button = page.locator('#form\\:btnSuche')
                await search_button.wait_for(timeout=10000)
                await search_button.click()
                await page.wait_for_timeout(5000)
            except Exception as e:
                print(f"   ❌ Search button not found: {e}")
                return
            
            print("5. Analyzing search results...")
            
            # Wait longer for results to load
            await page.wait_for_timeout(3000)
            
            # Debug: save screenshot to see what's on the page
            try:
                await page.screenshot(path="debug_results.png")
                print("   📸 Saved debug screenshot: debug_results.png")
            except Exception as e:
                print(f"   ⚠️  Could not save screenshot: {e}")
            
            # Look for the actual document table structure
            try:
                table_info = await page.evaluate("""
                    () => {
                        // Look for tables that might contain documents
                        const tables = Array.from(document.querySelectorAll('table'));
                        console.log('Found tables:', tables.length);
                        
                        let tableData = [];
                        tables.forEach((table, index) => {
                            const rows = Array.from(table.querySelectorAll('tr'));
                            const hasAdCd = rows.some(row => 
                                row.textContent.includes('AD') || row.textContent.includes('CD')
                            );
                            
                            if (hasAdCd) {
                                console.log(`Table ${index} has AD/CD content`);
                                
                                // Look for document links within this table
                                const docLinks = [];
                                rows.forEach((row, rowIndex) => {
                                    const links = Array.from(row.querySelectorAll('a'));
                                    links.forEach(link => {
                                        const text = link.textContent.trim();
                                        if (text === 'AD' || text === 'CD') {
                                            docLinks.push({
                                                row: rowIndex,
                                                text: text,
                                                id: link.id,
                                                onclick: link.onclick ? link.onclick.toString() : '',
                                                className: link.className
                                            });
                                        }
                                    });
                                });
                                
                                tableData.push({
                                    index: index,
                                    rows: rows.length,
                                    hasAdCd: hasAdCd,
                                    docLinks: docLinks,
                                    content: rows.map(row => row.textContent.trim().substring(0, 100))
                                });
                            }
                        });
                        
                        return tableData;
                    }
                """)
                
                print(f"   📊 Found {len(table_info)} tables with AD/CD content")
                if table_info:
                    for table in table_info:
                        print(f"      Table {table['index']}: {table['rows']} rows, {len(table['docLinks'])} document links")
                        if table['docLinks']:
                            print(f"         Document links: {table['docLinks']}")
                
                # Use the document links found in tables if available
                if table_info and table_info[0]['docLinks']:
                    document_links = table_info[0]['docLinks']
                    print(f"   🎯 Using {len(document_links)} document links from table")
                else:
                    # Fallback to the old method
                    document_links = await page.evaluate("""
                        () => {
                            // Try multiple selectors for document links
                            let links = [];
                            
                            // Method 1: Look for links with AD/CD text
                            const adcdLinks = Array.from(document.querySelectorAll('a')).filter(link => {
                                const text = link.textContent.trim();
                                return text === 'AD' || text === 'CD';
                            });
                            
                            // Method 2: Look for links with onclick containing 'PrimeFaces'
                            const primefacesLinks = Array.from(document.querySelectorAll('a')).filter(link => {
                                return link.onclick && link.onclick.toString().includes('PrimeFaces');
                            });
                            
                            // Method 3: Look for any links that might be documents
                            const allLinks = Array.from(document.querySelectorAll('a')).filter(link => {
                                const text = link.textContent.trim();
                                return text && text.length <= 5 && /^[A-Z]+$/.test(text);
                            });
                            
                            // Method 4: Look for links in table cells
                            const tableLinks = Array.from(document.querySelectorAll('td a')).filter(link => {
                                const text = link.textContent.trim();
                                return text === 'AD' || text === 'CD';
                            });
                            
                            console.log('AD/CD links:', adcdLinks.length);
                            console.log('PrimeFaces links:', primefacesLinks.length);
                            console.log('Short uppercase links:', allLinks.length);
                            console.log('Table AD/CD links:', tableLinks.length);
                            
                            // Combine all methods, prioritize table links
                            const allFound = [...tableLinks, ...adcdLinks, ...primefacesLinks, ...allLinks];
                            const uniqueLinks = allFound.filter((link, index, self) => 
                                self.findIndex(l => l.id === link.id) === index
                            );
                            
                            return uniqueLinks.map(link => ({
                                id: link.id,
                                text: link.textContent.trim(),
                                onclick: link.onclick ? link.onclick.toString() : '',
                                className: link.className,
                                visible: link.offsetParent !== null
                            }));
                        }
                    """)
                
                # Also try to find any links with different selectors
                all_links = await page.evaluate("""
                    () => {
                        const allLinks = Array.from(document.querySelectorAll('a'));
                        return allLinks.map(link => ({
                            id: link.id,
                            text: link.textContent.trim(),
                            className: link.className,
                            href: link.href
                        })).filter(link => link.text && link.text.length < 10);
                    }
                """)
                
                print(f"   🔍 Found {len(all_links)} total links on page")
                if all_links:
                    print(f"   📝 Sample links: {all_links[:5]}")
                
                print(f"   📋 Found {len(document_links)} potential document links")
                if document_links:
                    print(f"   📄 Document link details: {document_links[:3]}")
                
            except Exception as e:
                print(f"   ❌ Failed to extract document links: {e}")
                return
            
            if document_links:
                print(f"   ✅ Found {len(document_links)} document links")
                
                # Extract company names AND registration numbers from the page
                company_data = await page.evaluate("""
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
                                
                                // Look for company name and registration number in ALL cells of the row
                                const cells = row.querySelectorAll('td');
                                if (cells.length > 0) {
                                    // Check all cells for company names and registration numbers
                                    for (let i = 0; i < cells.length; i++) {
                                        const cell = cells[i];
                                        const text = cell.textContent.trim();
                                        
                                        // Look for registration number (HRB format) - PRIORITY 1
                                        if (text && text.includes('HRB') && /HRB\\s*\\d+/.test(text)) {
                                            const hrbMatch = text.match(/HRB\\s*(\\d+)/);
                                            if (hrbMatch) {
                                                registrationNumber = hrbMatch[1];
                                                console.log('Found HRB number:', registrationNumber);
                                            }
                                        }
                                        
                                        // Look for text that contains company-like patterns (but not registration numbers)
                                        if (text && 
                                            text.length > 5 &&  // Reduced minimum length
                                            /[a-zA-Z]/.test(text) &&  // Must contain letters
                                            !text.includes('1.)') && 
                                            !text.includes('2.)') && 
                                            !text.includes('3.)') && 
                                            !text.includes('Historie') &&
                                            !text.includes('DE') &&
                                            !text.includes('EN') &&
                                            !text.includes('ES') &&
                                            !text.includes('FR') &&
                                            !text.includes('AD') &&
                                            !text.includes('CD') &&
                                            !text.includes('j_idt') &&
                                            !text.includes('onclick') &&
                                            !text.includes('function') &&
                                            !text.includes('PrimeFaces') &&
                                            !text.includes('submit') &&
                                            !text.includes('return') &&
                                            !text.includes('false') &&
                                            !text.includes('event') &&
                                            !text.includes('property') &&
                                            !text.includes('property2') &&
                                            !text.includes('Global') &&
                                            !text.includes('Dokumentart') &&
                                            !text.includes('ergebnissForm') &&
                                            !text.includes('selectedSuchErgebnisFormTable') &&
                                            !text.includes('fade_') &&
                                            !text.includes('ui-commandlink') &&
                                            !text.includes('ui-widget') &&
                                            !text.includes('dokumentList') &&
                                            !text.includes('ui-corner-all') &&
                                            !text.includes('ui-menuitem-link') &&
                                            !text.includes('ui-submenu-link') &&
                                            !text.includes('District court') &&
                                            !text.includes('Amtsgericht') &&
                                            !text.includes('Frankfurt am Main') &&  // Exclude location names
                                            !text.includes('Hesse') &&  // Exclude state names
                                            !/HRB\\s*\\d+/.test(text)) {  // Exclude HRB numbers from company names
                                            
                                            // Clean up the text - remove extra whitespace and newlines
                                            const cleanText = text.replace(/\\s+/g, ' ').trim();
                                            if (cleanText.length > 5) {
                                                companyName = cleanText;
                                                console.log('Found company name:', cleanText);
                                            }
                                        }
                                        
                                        // Fallback: Look for business-related keywords that might indicate company names
                                        if (!companyName && text && 
                                            text.length > 5 && 
                                            /[a-zA-Z]/.test(text) &&
                                            (text.includes('Bank') || 
                                             text.includes('GmbH') || 
                                             text.includes('AG') || 
                                             text.includes('KG') || 
                                             text.includes('OHG') ||
                                             text.includes('Deutsche') ||
                                             text.includes('Aktiengesellschaft') ||
                                             text.includes('Gesellschaft')) &&
                                            !text.includes('HRB') &&
                                            !text.includes('Frankfurt am Main') &&
                                            !text.includes('Hesse')) {
                                            
                                            const cleanText = text.replace(/\\s+/g, ' ').trim();
                                            companyName = cleanText;
                                            console.log('Found company name (fallback):', cleanText);
                                        }
                                    }
                                    
                                    // If we found both company name and registration number, add them
                                    if (companyName && registrationNumber) {
                                        companies.push({
                                            name: companyName,
                                            hrb: registrationNumber
                                        });
                                        console.log('Added company:', companyName, 'HRB:', registrationNumber);
                                    }
                                }
                            }
                        });
                        
                        console.log('Total companies found:', companies.length);
                        return companies;
                    }
                """)
                
                # Convert the company data to a more usable format
                company_names = [f"{company['name']} (HRB {company['hrb']})" for company in company_data]
                company_hrb_map = {company['name']: company['hrb'] for company in company_data}
                
                print(f"   📊 Found companies: {len(company_names)} total")
                print("   📋 All companies found:")
                for i, company in enumerate(company_names):
                    print(f"      {i+1:2d}. {company}")
                
                # Find the best matching company using both name and registration number
                def find_best_match(search_name, company_data_list, company_hrb_map, target_registration=None):
                    """Find the company that best matches the search name with smart legal form handling and registration number matching"""
                    
                    if target_registration:
                        print(f"   🔢 Target registration number: {target_registration}")
                    else:
                        print(f"   🔍 No target registration number specified")
                    
                    # Legal form mappings (full names to abbreviations)
                    legal_form_mappings = {
                        'aktien': 'ag',
                        'gesellschaft mit beschränkter haftung': 'gmbh',
                        'gesellschaft mit beschraenkter haftung': 'gmbh',  # German umlaut alternative
                        'offene handelsgesellschaft': 'ohg',
                        'kommanditgesellschaft': 'kg',
                        'eingetragener verein': 'ev',
                        'eingetragene genossenschaft': 'eg',
                        'gesellschaft bürgerlichen rechts': 'gbr',
                        'gesellschaft buergerlichen rechts': 'gbr',  # German umlaut alternative
                        'partnerschaftsgesellschaft': 'partg',
                        'europäische wirtschaftliche interessenvereinigung': 'ewiv',
                        'europaeische wirtschaftliche interessenvereinigung': 'ewiv',  # German umlaut alternative
                        'europäische aktiengesellschaft': 'se',
                        'europaeische aktiengesellschaft': 'se',  # German umlaut alternative
                    }
                    
                    # Create normalized versions of search name and company names
                    def normalize_company_name(name):
                        """Normalize company name by standardizing legal forms and removing common noise"""
                        name_lower = name.lower().strip()
                        
                        # Replace full legal form names with abbreviations
                        for full_form, abbrev in legal_form_mappings.items():
                            name_lower = name_lower.replace(full_form, abbrev)
                        
                        # Remove common noise words and punctuation
                        noise_words = ['hrb', 'amtsgericht', 'register', 'handelsregister', 'commercial register']
                        for noise in noise_words:
                            name_lower = name_lower.replace(noise, '')
                        
                        # Clean up extra spaces and punctuation
                        import re
                        name_lower = re.sub(r'[^\w\s]', ' ', name_lower)
                        name_lower = re.sub(r'\s+', ' ', name_lower).strip()
                        
                        return name_lower
                    
                    search_name_normalized = normalize_company_name(search_name)
                    best_match = None
                    best_score = 0
                    
                    # Debug: print what we're searching for
                    print(f"   🔍 Searching for normalized: '{search_name_normalized}'")
                    
                    # Extract core business words (excluding legal forms)
                    legal_forms = set(['ag', 'gmbh', 'ohg', 'kg', 'ev', 'eg', 'gbr', 'partg', 'ewiv', 'se'])
                    search_words = set(search_name_normalized.split())
                    core_search_words = [word for word in search_words if word not in legal_forms]
                    
                    print(f"   🎯 Core business words: {core_search_words}")
                    
                    for company_full in company_data_list:
                        # Extract company name and HRB number from the full string
                        import re
                        company_match = re.match(r'(.+?)\s*\(HRB\s*(\d+)\)', company_full)
                        if not company_match:
                            continue
                            
                        company_name = company_match.group(1).strip()
                        company_hrb = company_match.group(2)
                        
                        company_normalized = normalize_company_name(company_name)
                        company_words = set(company_normalized.split())
                        core_company_words = [word for word in company_words if word not in legal_forms]
                        
                        # Calculate base score from name matching
                        name_score = 0
                        
                        # Exact match gets highest score
                        if search_name_normalized == company_normalized:
                            name_score = 100
                            print(f"   🎯 Exact name match found: '{company_name}'")
                        
                        # HIGHEST PRIORITY: Check if ALL core search words are contained in company name
                        elif core_search_words and all(search_word in company_normalized for search_word in core_search_words):
                            name_score = 95 + (len(core_search_words) * 2)  # Base 95 + bonus for each matching word
                            print(f"   🏆 ALL core words match: '{company_name}' (name score: {name_score:.1f})")
                        
                        # HIGH PRIORITY: Check if search name is contained in company name
                        elif search_name_normalized in company_normalized:
                            name_score = 90 + (len(search_name_normalized) / len(company_normalized) * 5)
                            print(f"   📈 Search contained in company: '{company_name}' (name score: {name_score:.1f})")
                        
                        # MEDIUM PRIORITY: Check if company name is contained in search name
                        elif company_normalized in search_name_normalized:
                            name_score = 80 + (len(company_normalized) / len(search_name_normalized) * 5)
                            print(f"   📈 Company contained in search: '{company_name}' (name score: {name_score:.1f})")
                        
                        # Check for word matches with legal form awareness
                        else:
                            common_words = search_words.intersection(company_words)
                            if common_words:
                                name_score = len(common_words) / max(len(search_words), len(company_words)) * 60
                                print(f"   📈 Word match: '{company_name}' (name score: {name_score:.1f})")
                            
                            # Check for partial word matches
                            else:
                                for search_word in search_words:
                                    for company_word in company_words:
                                        if search_word in company_word or company_word in search_word:
                                            name_score = min(len(search_word), len(company_word)) / max(len(search_word), len(company_word)) * 50
                                            print(f"   📈 Partial word match: '{company_name}' (name score: {name_score:.1f})")
                                            break
                                    if name_score > 0:
                                        break
                        
                        # Calculate final score with HRB number prioritization
                        # First, check if we have a target HRB number to match against
                        # For now, we'll prioritize companies with any HRB number over those without
                        # In the future, if we have a specific target HRB, we can add that logic here
                        
                        # Registration number prioritization - this is the PRIMARY matching criteria
                        registration_bonus = 0
                        if company_hrb:
                            # If we have a target registration number, this is the PRIMARY match
                            if target_registration and company_hrb == target_registration:
                                registration_bonus = 1000  # Massive priority for exact registration match
                                print(f"   🎯 EXACT REGISTRATION MATCH! Target: {target_registration}, Company: {company_hrb} - PRIORITY 1")
                            else:
                                registration_bonus = 100  # Good bonus for having any registration number
                        else:
                            # No registration number - this company gets lower priority
                            registration_bonus = -50  # Penalty for no registration number
                        
                        # Calculate final score: registration matching is PRIMARY, name matching is secondary
                        final_score = registration_bonus + (name_score * 0.1)  # Registration gets 10x more weight than name
                        
                        # Add HRB number information to the output for better identification
                        company_display = f"{company_name} (HRB {company_hrb})"
                        
                        # Debug: show scoring breakdown
                        print(f"   📊 Scoring for '{company_display}': name_score={name_score:.1f}, registration_bonus={registration_bonus}, final_score={final_score:.1f}")
                        
                        if final_score > best_score:
                            best_score = final_score
                            best_match = company_display
                            print(f"   🏆 NEW BEST MATCH: '{company_display}' (final score: {final_score:.1f})")
                    
                    print(f"   🏆 Final best match: '{best_match}' (final score: {best_score:.1f})")
                    
                    # If no registration match found, try to find any company by name only
                    if not best_match and target_registration:
                        print(f"   🔄 No registration {target_registration} match found, falling back to name-only matching...")
                        for company_full in company_data_list:
                            company_match = re.match(r'(.+?)\s*\(HRB\s*(\d+)\)', company_full)
                            if company_match:
                                company_name = company_match.group(1).strip()
                                company_hrb = company_match.group(2)
                                
                                company_normalized = normalize_company_name(company_name)
                                
                                # Simple name matching as fallback
                                if search_name_normalized in company_normalized or company_normalized in search_name_normalized:
                                    company_display = f"{company_name} (HRB {company_hrb})"
                                    print(f"   🔄 Fallback match found: '{company_display}'")
                                    return company_display, 50  # Lower score for fallback
                    
                    return best_match, best_score
                
                # Find the best matching company
                best_company, match_score = find_best_match(company_name, company_names, company_hrb_map, registration_number)
                
                if best_company:
                    print(f"   🎯 Best match: '{best_company}' (score: {match_score:.1f})")
                    
                    # Extract company name and HRB number from the best match
                    import re
                    company_match = re.match(r'(.+?)\s*\(HRB\s*(\d+)\)', best_company)
                    if company_match:
                        company_name_only = company_match.group(1).strip()
                        company_hrb = company_match.group(2)
                        print(f"   🏢 Company: {company_name_only}")
                        print(f"   🔢 HRB Number: {company_hrb}")
                    else:
                        company_name_only = best_company
                        company_hrb = None
                        print(f"   🏢 Company: {company_name_only}")
                        print(f"   ⚠️  No HRB number found")
                    
                    # Filter documents to only those belonging to the best matching company
                    # We need to find the specific AD and CD documents for this company
                    company_documents = []
                    
                    # Find AD and CD documents for this company by looking for rows that contain the registration number
                    # Since registration numbers are unique, this is more reliable than company name matching
                    company_docs = await page.evaluate("""
                        (registrationNumber) => {
                            const docs = [];
                            const companyNames = [];
                            const tableRows = document.querySelectorAll('tr');
                            
                            tableRows.forEach(row => {
                                const rowText = row.textContent;
                                // Check if this row contains the specific registration number
                                if (registrationNumber && rowText.includes('HRB ' + registrationNumber)) {
                                    // Extract company name from this row
                                    const cells = row.querySelectorAll('td');
                                    cells.forEach(cell => {
                                        const text = cell.textContent.trim();
                                        // Look for company names (not registration numbers, not navigation text)
                                        if (text && 
                                            text.length > 5 && 
                                            /[a-zA-Z]/.test(text) &&
                                            !text.includes('HRB') &&
                                            !text.includes('Frankfurt am Main') &&
                                            !text.includes('Hesse') &&
                                            !text.includes('aktuell') &&
                                            !text.includes('1.)') &&
                                            !text.includes('2.)') &&
                                            !text.includes('3.)') &&
                                            !text.includes('AD') &&
                                            !text.includes('CD')) {
                                            companyNames.push(text);
                                        }
                                    });
                                    
                                    // Find all AD and CD links in this row
                                    const links = row.querySelectorAll('a[id*="j_idt"]');
                                    links.forEach(link => {
                                        const text = link.textContent.trim();
                                        if (text === 'AD' || text === 'CD') {
                                            docs.push({
                                                id: link.id,
                                                text: text,
                                                href: link.href
                                            });
                                        }
                                    });
                                }
                            });
                            
                            return { docs: docs, companyNames: companyNames };
                        }
                    """, company_hrb)
                    
                    # Extract documents and company names from the results
                    if isinstance(company_docs, dict) and 'docs' in company_docs:
                        docs_list = company_docs['docs']
                        extracted_company_names = company_docs.get('companyNames', [])
                    else:
                        docs_list = company_docs
                        extracted_company_names = []
                    
                    # Use extracted company name if available, otherwise fall back to the matched name
                    actual_company_name = extracted_company_names[0] if extracted_company_names else company_name_only
                    
                    for doc in docs_list:
                        company_documents.append({
                            'link': doc,
                            'doc_type': doc['text'],
                            'company': actual_company_name
                        })
                    
                    print(f"   📥 Found {len(company_documents)} AD/CD documents for '{actual_company_name}'")
                    
                    # Download only documents for the best matching company
                    downloaded = 0
                    
                    for i, doc_info in enumerate(company_documents):
                        try:
                            doc_type = doc_info['doc_type']
                            company_name_clean = doc_info['company']
                            
                            print(f"   📥 Downloading {doc_type} for: {company_name_clean[:50]}...")
                            
                            # Click the document link using attribute selector to avoid CSS escaping issues
                            link_element = page.locator(f'a[id="{doc_info["link"]["id"]}"]')
                            
                            # Set up download listener before clicking
                            try:
                                async with page.expect_download(timeout=45000) as download_info:
                                    await link_element.click()
                                    # Wait a bit for the download to start
                                    await page.wait_for_timeout(1000)
                                
                                download = await download_info.value
                            except Exception as download_error:
                                print(f"   ⚠️  Download timeout, trying alternative method...")
                                # Try clicking without waiting for download event
                                await link_element.click()
                                await page.wait_for_timeout(3000)
                                # Check if we can find the download in the browser's download list
                                downloads = await page.context.downloads()
                                if downloads:
                                    download = downloads[-1]  # Get the most recent download
                                else:
                                    raise download_error
                            
                            # Create safe filename
                            safe_company = "".join(c for c in company_name_clean if c.isalnum() or c in (' ', '-', '_')).strip()
                            safe_company = safe_company.replace(' ', '_')[:30]
                            filename = f"{safe_company}_{doc_type}.pdf"
                            
                            # Save the download
                            await download.save_as(f"downloads/{filename}")
                            print(f"   ✅ Saved: {filename}")
                            downloaded += 1
                            
                            # Wait between downloads to be polite
                            await page.wait_for_timeout(3000)
                            
                            # Check if page is still responsive
                            try:
                                await page.wait_for_function("document.readyState === 'complete'", timeout=10000)
                            except:
                                print(f"   ⚠️  Page not fully loaded, continuing...")
                        
                        except Exception as e:
                            print(f"   ❌ Download {i+1} failed: {e}")
                            continue
                    
                    print(f"\n🎉 Successfully downloaded {downloaded} documents for '{best_company}'!")
                else:
                    print("   ❌ No matching company found")
                    print(f"   📝 Available companies: {company_names}")
                
            else:
                print("   ❌ No document links found")
                
                # Debug: save page and check for error messages
                try:
                    await page.screenshot(path="debug_no_docs.png")
                    content = await page.content()
                    with open("debug_no_docs.html", "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    print(f"   ⚠️  Could not save debug files: {e}")
                
                # Check for any error or info messages
                try:
                    messages = await page.evaluate("""
                        () => {
                            const messageSelectors = ['.ui-messages', '.ui-message', '.error', '.warning', '.info'];
                            let messages = [];
                            messageSelectors.forEach(selector => {
                                document.querySelectorAll(selector).forEach(el => {
                                    if (el.textContent.trim()) {
                                        messages.push(el.textContent.trim());
                                    }
                                });
                            });
                            return messages;
                        }
                    """)
                    
                    if messages:
                        print(f"   📝 Page messages: {messages}")
                except Exception as e:
                    print(f"   ⚠️  Could not extract messages: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            try:
                await page.screenshot(path="error_working.png")
            except:
                print("   ⚠️  Could not save error screenshot")
        finally:
            await browser.close()
            print("🔚 Done!")

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python scraper_working.py 'company name' [registration_number]")
        print("Examples:")
        print("  python scraper_working.py 'Deutsche Bank AG'")
        print("  python scraper_working.py 'Deutsche Bank AG' '30000'")
        sys.exit(1)
    
    company_name = sys.argv[1]
    registration_number = sys.argv[2] if len(sys.argv) == 3 else None
    
    # Create downloads directory if it doesn't exist
    pathlib.Path("downloads").mkdir(exist_ok=True)
    
    asyncio.run(search_and_download(company_name, registration_number))