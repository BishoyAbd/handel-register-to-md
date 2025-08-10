#!/usr/bin/env python3
"""
Simple pipeline that runs the complete workflow:
1. Download PDFs using pdf_scraper.py
2. Extract tables using pdf_extractor.py
"""

import asyncio
import sys
from pdf_scraper import search_and_download
from pdf_extractor import PDFTableExtractor

async def run_pipeline(company_name: str):
    """Run the complete pipeline for a company"""
    print(f"🚀 Starting pipeline for: {company_name}")
    print("=" * 50)
    
    # Step 1: Download PDFs
    print("📥 Step 1: Downloading PDFs...")
    downloaded_pdfs = await search_and_download(company_name)
    
    if not downloaded_pdfs:
        print("❌ No PDFs downloaded. Pipeline failed.")
        return
    
    print(f"   ✅ Downloaded {len(downloaded_pdfs)} PDFs: {', '.join(downloaded_pdfs)}")
    
    # Step 2: Extract tables from PDFs in memory
    print("📊 Step 2: Extracting tables...")
    extractor = PDFTableExtractor()
    
    # Process PDFs directly from memory
    markdown_files = []
    for pdf_data in downloaded_pdfs:
        try:
            # Extract tables from PDF bytes
            extracted_data = extractor.extract_tables_from_pdf_bytes(pdf_data)
            
            # Save to markdown
            markdown_filename = f"{pdf_data['filename'].replace('.pdf', '_enriched.md')}"
            markdown_path = extractor.output_dir / markdown_filename
            
            # Save the extracted data
            extractor.save_to_markdown(extracted_data, markdown_filename)
            
            markdown_files.append(str(markdown_path))
            print(f"   ✅ Processed: {pdf_data['filename']}")
        except Exception as e:
            print(f"   ❌ Failed to process {pdf_data['filename']}: {e}")
    
    print(f"✅ Pipeline completed!")
    print(f"   📝 Created {len(markdown_files)} markdown files")

async def main():
    if len(sys.argv) != 2:
        print("Usage: python pipeline.py 'company name'")
        print("Example: python pipeline.py 'CHECK24'")
        sys.exit(1)
    
    company_name = sys.argv[1]
    await run_pipeline(company_name)

if __name__ == "__main__":
    asyncio.run(main())
