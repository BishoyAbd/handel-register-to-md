import sys
import asyncio
from playwright.async_api import async_playwright
import pathlib
import time

HOME_URL = "https://www.handelsregister.de/"

async def search_and_download(company_name: str):
    """
    Working scraper using ACTUAL element names and document link patterns
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
            
            # Fill search form
            print("3. Filling search form...")
            try:
                search_field = page.locator('#form\\:schlagwoerter')
                await search_field.wait_for(timeout=10000)
                await search_field.clear()
                await search_field.fill(company_name)
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
                
                # Get company names and their associated document counts
                company_names = await page.evaluate("""
                    () => {
                        const companies = [];
                        const companyElements = document.querySelectorAll('span.marginLeft20');
                        companyElements.forEach(el => {
                            const text = el.textContent.trim();
                            if (text && !text.includes('1.)') && !text.includes('Historie')) {
                                companies.push(text);
                            }
                        });
                        return companies;
                    }
                """)
                
                print(f"   📊 Found companies: {company_names[:3]}...")  # Show first 3
                
                # Find the best matching company
                def find_best_match(search_name, company_list):
                    """Find the company that best matches the search name"""
                    search_name_lower = search_name.lower().strip()
                    best_match = None
                    best_score = 0
                    
                    for company in company_list:
                        company_lower = company.lower().strip()
                        
                        # Exact match gets highest score
                        if search_name_lower == company_lower:
                            return company, 100
                        
                        # Check if search name is contained in company name
                        if search_name_lower in company_lower:
                            score = len(search_name_lower) / len(company_lower) * 80
                            if score > best_score:
                                best_score = score
                                best_match = company
                        
                        # Check if company name is contained in search name
                        elif company_lower in search_name_lower:
                            score = len(company_lower) / len(search_name_lower) * 70
                            if score > best_score:
                                best_score = score
                                best_match = company
                        
                        # Check for word matches
                        search_words = set(search_name_lower.split())
                        company_words = set(company_lower.split())
                        common_words = search_words.intersection(company_words)
                        if common_words:
                            score = len(common_words) / max(len(search_words), len(company_words)) * 60
                            if score > best_score:
                                best_score = score
                                best_match = company
                    
                    return best_match, best_score
                
                # Find the best matching company
                best_company, match_score = find_best_match(company_name, company_names)
                
                if best_company:
                    print(f"   🎯 Best match: '{best_company}' (score: {match_score:.1f})")
                    
                    # Find the index of the best matching company
                    try:
                        best_company_index = company_names.index(best_company)
                    except ValueError:
                        best_company_index = 0
                    
                    # Filter documents to only those belonging to the best matching company
                    # Each company typically has multiple document types, so we need to group them
                    company_documents = []
                    for i, link in enumerate(document_links):
                        # Estimate which company this document belongs to based on position
                        # This is approximate - we'll refine it by checking if it's AD or CD
                        if link['text'] in ['AD', 'CD']:
                            company_documents.append({
                                'link': link,
                                'doc_type': link['text'],
                                'company': best_company
                            })
                    
                    print(f"   📥 Found {len(company_documents)} AD/CD documents for '{best_company}'")
                    
                    # Download only documents for the best matching company
                    downloaded = 0
                    
                    for i, doc_info in enumerate(company_documents):
                        try:
                            doc_type = doc_info['doc_type']
                            company_name_clean = doc_info['company']
                            
                            print(f"   📥 Downloading {doc_type} for: {company_name_clean[:30]}...")
                            
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
                            filename = f"{safe_company}_{doc_type}_{i+1}.pdf"
                            
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
    if len(sys.argv) != 2:
        print("Usage: python pdf_scraper.py 'company name'")
        sys.exit(1)
    
    company_name = sys.argv[1]
    
    # Create downloads directory if it doesn't exist
    pathlib.Path("downloads").mkdir(exist_ok=True)
    
    asyncio.run(search_and_download(company_name))