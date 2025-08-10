import sys
import asyncio
from playwright.async_api import async_playwright
import json

HOME_URL = "https://www.handelsregister.de/"

async def diagnose_page():
    """
    Systematically examine the page structure to find actual element names
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        try:
            print("🔍 PHASE 1: Examining Homepage")
            await page.goto(HOME_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Find all navigation links
            print("\n📋 All navigation links on homepage:")
            nav_links = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return links.map(link => ({
                        text: link.textContent.trim(),
                        href: link.href,
                        id: link.id,
                        className: link.className,
                        onclick: link.onclick ? link.onclick.toString() : '',
                        title: link.title
                    })).filter(link => 
                        link.text.toLowerCase().includes('such') || 
                        link.text.toLowerCase().includes('search') ||
                        link.title.toLowerCase().includes('such') ||
                        link.onclick.toLowerCase().includes('such')
                    );
                }
            """)
            
            for i, link in enumerate(nav_links):
                print(f"{i+1}. Text: '{link['text'][:50]}...'")
                print(f"   ID: {link['id']}")
                print(f"   Class: {link['className']}")
                print(f"   Title: {link['title']}")
                print(f"   Onclick: {link['onclick'][:100]}...")
                print()
            
            # Try clicking the main navigation link
            print("🔍 PHASE 2: Navigating to search page")
            main_nav_link = page.locator('#naviForm\\:normaleSucheLink')
            if await main_nav_link.count() > 0:
                await main_nav_link.click()
                print("✅ Clicked main nav link")
                await page.wait_for_timeout(3000)
                
                # Check current URL and title
                current_url = page.url
                title = await page.title()
                print(f"Current URL: {current_url}")
                print(f"Page Title: {title}")
                
                print("\n🔍 PHASE 3: Examining search page structure")
                
                # Find all forms
                print("\n📋 All forms on search page:")
                forms = await page.evaluate("""
                    () => {
                        const forms = Array.from(document.querySelectorAll('form'));
                        return forms.map(form => ({
                            id: form.id,
                            action: form.action,
                            method: form.method,
                            className: form.className
                        }));
                    }
                """)
                
                for i, form in enumerate(forms):
                    print(f"{i+1}. ID: {form['id']}")
                    print(f"   Action: {form['action']}")
                    print(f"   Method: {form['method']}")
                    print(f"   Class: {form['className']}")
                    print()
                
                # Find all input fields
                print("📋 All input fields on search page:")
                inputs = await page.evaluate("""
                    () => {
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        return inputs.map(input => ({
                            type: input.type,
                            name: input.name,
                            id: input.id,
                            className: input.className,
                            placeholder: input.placeholder,
                            value: input.value,
                            visible: input.offsetParent !== null
                        }));
                    }
                """)
                
                for i, inp in enumerate(inputs):
                    print(f"{i+1}. Type: {inp['type']}")
                    print(f"   Name: {inp['name']}")
                    print(f"   ID: {inp['id']}")
                    print(f"   Class: {inp['className']}")
                    print(f"   Placeholder: {inp['placeholder']}")
                    print(f"   Visible: {inp['visible']}")
                    print()
                
                # Find all buttons
                print("📋 All buttons on search page:")
                buttons = await page.evaluate("""
                    () => {
                        const buttons = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"]'));
                        return buttons.map(button => ({
                            type: button.type,
                            name: button.name,
                            id: button.id,
                            className: button.className,
                            text: button.textContent ? button.textContent.trim() : button.value,
                            visible: button.offsetParent !== null
                        }));
                    }
                """)
                
                for i, btn in enumerate(buttons):
                    print(f"{i+1}. Type: {btn['type']}")
                    print(f"   Name: {btn['name']}")
                    print(f"   ID: {btn['id']}")
                    print(f"   Class: {btn['className']}")
                    print(f"   Text: {btn['text']}")
                    print(f"   Visible: {btn['visible']}")
                    print()
                
                # Save current page HTML for further inspection
                content = await page.content()
                with open("diagnose_search_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("💾 Saved search page HTML as 'diagnose_search_page.html'")
                
                # Save all data as JSON for easier analysis
                all_data = {
                    "url": current_url,
                    "title": title,
                    "forms": forms,
                    "inputs": inputs,
                    "buttons": buttons
                }
                
                with open("diagnose_data.json", "w", encoding="utf-8") as f:
                    json.dump(all_data, f, indent=2, ensure_ascii=False)
                print("💾 Saved diagnostic data as 'diagnose_data.json'")
                
            else:
                print("❌ Could not find main nav link")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="diagnose_error.png")
        finally:
            await browser.close()
            print("🔚 Diagnosis complete!")

if __name__ == "__main__":
    asyncio.run(diagnose_page())


