import asyncio
import argparse
from .app import ScraperApp
from .logger import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Scrape company documents from Handelsregister.")
    parser.add_argument("company_name", type=str, help="The name of the company to search for.")
    parser.add_argument("registration_number", type=str, nargs='?', default=None, help="The registration number (HRB) of the company.")
    parser.add_argument("--show-browser", action="store_true", help="Run the browser in visible mode (not headless).")
    args = parser.parse_args()

    # Default to headless=True, unless --show-browser is passed
    app = ScraperApp(headless=not args.show_browser)
    
    try:
        extracted_data = asyncio.run(app.run(args.company_name, args.registration_number))
        
        if extracted_data:
            print("\n--- In-Memory Extracted Data ---")
            for doc_type, content in extracted_data.items():
                print(f"\n--- Document: {doc_type} ---")
                # Print first 300 characters as a preview
                print(content[:300] + "...")
            print("\n---------------------------------")
        else:
            print("\nNo data was extracted.")
            
    except Exception as e:
        logger.critical(f"An unexpected error occurred in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()
