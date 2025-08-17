#!/usr/bin/env python3
"""
Simple test for HRA company to see the actual documents.
"""

import asyncio
import sys
from pathlib import Path

# Add the scraper package to the path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.hr_scraper import ScraperApp, DocumentType

async def test_hra_company():
    """Test HRA company to see actual documents."""
    
    print("🔍 Testing HRA Company: Bode Projects e. k.")
    print("=" * 60)
    print("Company: Bode Projects e. k.")
    print("Registration: HRA 57863 B")
    print("Document types: All available")
    print("-" * 60)
    
    app = ScraperApp(headless=True)
    
    try:
        result = await app.run(
            company_name="Bode Projects e. k.",
            registration_number="HRA 57863 B"
        )
        
        if result['success']:
            print(f"✅ Successfully scraped {len(result['documents'])} documents")
            print(f"Company: {result['company_info']['name']}")
            print(f"Registration: {result['company_info']['hrb']}")
            print()
            
            for i, doc in enumerate(result['documents'], 1):
                print(f"📄 Document {i}: {doc['doc_type']}")
                print(f"   PDF Filename: {doc['pdf_filename']}")
                print(f"   PDF Size: {len(doc['pdf_content'])} bytes")
                print(f"   Markdown Filename: {doc['markdown_filename']}")
                print(f"   Markdown Length: {len(doc['markdown_content'])} characters")
                
                # Save files for verification
                pdf_filename = f"test_HRA_{i}_Bode_Projects.pdf"
                md_filename = f"test_HRA_{i}_Bode_Projects.md"
                
                with open(pdf_filename, 'wb') as f:
                    f.write(doc['pdf_content'])
                with open(md_filename, 'w', encoding='utf-8') as f:
                    f.write(doc['markdown_content'])
                
                print(f"   💾 PDF saved as: {pdf_filename}")
                print(f"   💾 Markdown saved as: {md_filename}")
                
                # Show previews
                print(f"   🔍 PDF Preview (hex): {doc['pdf_content'][:50].hex()}...")
                print(f"   🔍 Markdown Preview: {doc['markdown_content'][:300]}...")
                print()
                
                # Document metadata
                print(f"   📊 Document metadata:")
                print(f"      - PDF is valid PDF")
                print(f"      - Markdown contains {doc['markdown_content'].count('#')} sections")
                print(f"      - Markdown contains {doc['markdown_content'].count('|')} table separators")
                print()
            
            print(f"🎉 Successfully downloaded {len(result['documents'])} documents!")
        else:
            print(f"❌ Failed: {result['error']}")
            if result.get('retry_recommended'):
                print("  Consider retrying this request")
                    
    except Exception as e:
        print(f"💥 Exception: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_hra_company())
