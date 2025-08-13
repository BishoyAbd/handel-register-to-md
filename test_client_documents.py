#!/usr/bin/env python3
"""
Test script to demonstrate that the client actually receives the downloaded documents
with different document type filtering options.
"""

import asyncio
from scraper.hr_scraper import ScraperApp, DocumentType

async def test_document_type_filtering():
    """Test different document type filtering options"""
    print("Testing Document Type Filtering")
    print("=" * 50)
    
    company_name = "Adler Real Estate GmbH"
    
    # Test 1: Download only AD documents
    print(f"\n🔍 Test 1: Downloading only AD documents for '{company_name}'")
    print("-" * 50)
    await test_specific_document_types(company_name, [DocumentType.AD])
    
    # Test 2: Download only CD documents
    print(f"\n🔍 Test 2: Downloading only CD documents for '{company_name}'")
    print("-" * 50)
    await test_specific_document_types(company_name, [DocumentType.CD])
    
    # Test 3: Download both AD and CD documents
    print(f"\n🔍 Test 3: Downloading both AD and CD documents for '{company_name}'")
    print("-" * 50)
    await test_specific_document_types(company_name, [DocumentType.AD, DocumentType.CD])
    
    # Test 4: Download all available documents (default)
    print(f"\n🔍 Test 4: Downloading all available documents for '{company_name}' (default)")
    print("-" * 50)
    await test_specific_document_types(company_name, None)

async def test_specific_document_types(company_name: str, document_types):
    """Test downloading specific document types"""
    try:
        # Create scraper instance
        app = ScraperApp(headless=True)
        
        # Show what we're requesting
        if document_types:
            doc_type_names = [dt.value for dt in document_types]
            print(f"📄 Requested document types: {doc_type_names}")
        else:
            print("📄 Requested document types: All available")
        
        # Run the scraper
        result = await app.run(company_name, document_types=document_types)
        
        # Check if successful
        if result['success']:
            print(f"✅ Successfully scraped {len(result['documents'])} documents")
            print(f"Company: {result['company_info']['name']}")
            print(f"HRB: {result['company_info']['hrb']}")
            
            # CLIENT ACTUALLY RECEIVES THESE DOCUMENTS!
            for i, doc in enumerate(result['documents'], 1):
                print(f"\n📄 Document {i}: {doc['doc_type']}")
                print(f"   PDF Filename: {doc['pdf_filename']}")
                print(f"   PDF Size: {len(doc['pdf_content'])} bytes")
                print(f"   Markdown Filename: {doc['markdown_filename']}")
                print(f"   Markdown Length: {len(doc['markdown_content'])} characters")
                
                # CLIENT CAN DO WHATEVER THEY WANT WITH THE DATA:
                
                # 1. Save PDF to file with descriptive naming
                pdf_filename = f"test_{doc['doc_type']}_{i}_{company_name.replace(' ', '_')}.pdf"
                with open(pdf_filename, 'wb') as f:
                    f.write(doc['pdf_content'])
                print(f"   💾 PDF saved as: {pdf_filename}")
                
                # 2. Save markdown to file with descriptive naming
                md_filename = f"test_{doc['doc_type']}_{i}_{company_name.replace(' ', '_')}.md"
                with open(md_filename, 'w', encoding='utf-8') as f:
                    f.write(doc['markdown_content'])
                print(f"   💾 Markdown saved as: {md_filename}")
                
                # 3. Show PDF content preview (first 100 bytes as hex)
                pdf_preview = doc['pdf_content'][:100].hex()
                print(f"   🔍 PDF Preview (hex): {pdf_preview[:50]}...")
                
                # 4. Show markdown content preview
                md_preview = doc['markdown_content'][:200]
                print(f"   🔍 Markdown Preview: {md_preview}...")
                
                # 5. Demonstrate other client operations
                print(f"   📊 Document metadata:")
                print(f"      - PDF is {'valid' if doc['pdf_content'].startswith(b'%PDF') else 'invalid'} PDF")
                print(f"      - Markdown contains {doc['markdown_content'].count('##')} sections")
                print(f"      - Markdown contains {doc['markdown_content'].count('|')} table separators")
            
            print(f"\n🎉 Successfully downloaded {len(result['documents'])} documents!")
            
        else:
            print(f"❌ Failed: {result['error']}")
            if result['retry_recommended']:
                print("  Consider retrying this request")
            else:
                print("  Do not retry - this is a permanent error")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all document type filtering tests"""
    print("HR Scraper - Document Type Filtering Test")
    print("=" * 50)
    
    try:
        await test_document_type_filtering()
        
        print(f"\n" + "=" * 50)
        print("All tests completed!")
        print("\nKey benefits of document type filtering:")
        print("1. Download only what you need (AD, CD, or both)")
        print("2. Save bandwidth and processing time")
        print("3. Focus on specific document types")
        print("4. Flexible control over scraping behavior")
        print("5. Easy to integrate into automated workflows")
        
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    asyncio.run(main())
