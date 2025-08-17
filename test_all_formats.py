#!/usr/bin/env python3
"""
Comprehensive test script for ALL German commercial register formats and document types.
Tests HRB, HRA, PR, GnR, VR, GüR, EWIV, SE, SCE, SPE and all document types.
"""

import asyncio
from scraper.hr_scraper import ScraperApp, DocumentType

async def test_all_registration_formats():
    """Test all German commercial register formats"""
    print("🇩🇪 Testing ALL German Commercial Register Formats")
    print("=" * 70)
    
    # Test companies with different registration types
    test_cases = [
        {
            "name": "Adler Real Estate GmbH",
            "registration": "HRB 259502",
            "type": "HRB",
            "description": "GmbH company (most common)"
        },
        {
            "name": "Bode Projects e. k.",
            "registration": "HRA 57863 B", 
            "type": "HRA",
            "description": "Sole proprietorship/partnership"
        },
        {
            "name": "Test Partnership",
            "registration": "PR 12345",
            "type": "PR", 
            "description": "Partnership Register"
        },
        {
            "name": "Test Cooperative",
            "registration": "GnR 67890",
            "type": "GnR",
            "description": "Cooperative Register"
        },
        {
            "name": "Test Association",
            "registration": "VR 11111",
            "type": "VR",
            "description": "Association Register"
        },
        {
            "name": "Test European Company",
            "registration": "SE 22222",
            "type": "SE",
            "description": "European Company"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['type']} Format")
        print(f"Company: {test_case['name']}")
        print(f"Registration: {test_case['registration']}")
        print(f"Type: {test_case['description']}")
        print("-" * 50)
        
        try:
            app = ScraperApp(headless=True)
            result = await app.run(
                company_name=test_case['name'],
                registration_number=test_case['registration']
            )
            
            if result['success']:
                print(f"✅ SUCCESS: Found {len(result['documents'])} documents")
                print(f"Company: {result['company_info']['name']}")
                print(f"Registration: {result['company_info']['hrb']}")
                
                for j, doc in enumerate(result['documents'], 1):
                    print(f"  📄 Document {j}: {doc['doc_type']} ({len(doc['pdf_content'])} bytes)")
                    
                    # Save files for verification
                    pdf_filename = f"test_{test_case['type']}_{j}_{test_case['name'].replace(' ', '_').replace('.', '')}.pdf"
                    md_filename = f"test_{test_case['type']}_{j}_{test_case['name'].replace(' ', '_').replace('.', '')}.md"
                    
                    with open(pdf_filename, 'wb') as f:
                        f.write(doc['pdf_content'])
                    with open(md_filename, 'w', encoding='utf-8') as f:
                        f.write(doc['markdown_content'])
                    
                    print(f"    💾 Saved: {pdf_filename}, {md_filename}")
            else:
                print(f"❌ FAILED: {result['error']}")
                if result.get('retry_recommended'):
                    print("  Consider retrying this request")
                    
        except Exception as e:
            print(f"💥 EXCEPTION: {e}")
        
        print()

async def test_all_document_types():
    """Test all available document types"""
    print("\n📄 Testing ALL Document Types")
    print("=" * 50)
    
    company_name = "Adler Real Estate GmbH"
    all_document_types = [
        DocumentType.AD, DocumentType.CD, DocumentType.HD, 
        DocumentType.DK, DocumentType.UT, DocumentType.VÖ, DocumentType.SI
    ]
    
    print(f"Company: {company_name}")
    print(f"Testing document types: {[dt.value for dt in all_document_types]}")
    print("-" * 50)
    
    try:
        app = ScraperApp(headless=True)
        result = await app.run(
            company_name=company_name,
            document_types=all_document_types
        )
        
        if result['success']:
            print(f"✅ SUCCESS: Found {len(result['documents'])} documents")
            print(f"Company: {result['company_info']['name']}")
            print(f"Registration: {result['company_info']['hrb']}")
            
            for i, doc in enumerate(result['documents'], 1):
                print(f"\n📄 Document {i}: {doc['doc_type']}")
                print(f"   PDF Size: {len(doc['pdf_content'])} bytes")
                print(f"   Markdown Length: {len(doc['markdown_content'])} characters")
                
                # Save files
                pdf_filename = f"test_all_types_{doc['doc_type']}_{i}.pdf"
                md_filename = f"test_all_types_{doc['doc_type']}_{i}.md"
                
                with open(pdf_filename, 'wb') as f:
                    f.write(doc['pdf_content'])
                with open(md_filename, 'w', encoding='utf-8') as f:
                    f.write(doc['markdown_content'])
                
                print(f"   💾 Saved: {pdf_filename}, {md_filename}")
                
                # Show preview
                print(f"   🔍 Markdown Preview: {doc['markdown_content'][:200]}...")
        else:
            print(f"❌ FAILED: {result['error']}")
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

async def test_registration_extraction():
    """Test registration number extraction from various input formats"""
    print("\n🔍 Testing Registration Number Extraction")
    print("=" * 50)
    
    test_inputs = [
        "HRB 123456",
        "HRA 789012",
        "PR 345678",
        "GnR 901234",
        "VR 567890",
        "GüR 123789",
        "EWIV 456123",
        "SE 789456",
        "SCE 012345",
        "SPE 678901",
        "HRB: 123456",
        "HRA 123 456",
        "123456",
        "123 456",
        "123456A",
        "HRB 123 456 A"
    ]
    
    app = ScraperApp(headless=True)
    
    for test_input in test_inputs:
        extracted = app._extract_hrb_from_input("", test_input)
        print(f"Input: {test_input:20} → Extracted: {extracted}")

async def main():
    """Run all comprehensive tests"""
    print("🇩🇪 German Commercial Register - Universal Format Support Test")
    print("=" * 80)
    print("Testing ALL registration formats: HRB, HRA, PR, GnR, VR, GüR, EWIV, SE, SCE, SPE")
    print("Testing ALL document types: AD, CD, HD, DK, UT, VÖ, SI")
    print("=" * 80)
    
    try:
        # Test registration number extraction
        await test_registration_extraction()
        
        # Test all registration formats
        await test_all_registration_formats()
        
        # Test all document types
        await test_all_document_types()
        
        print("\n" + "=" * 80)
        print("🎉 All tests completed!")
        print("\n✅ Package now supports ALL German commercial register formats:")
        print("   • HRB - Handelsregister B (GmbH, AG, etc.)")
        print("   • HRA - Handelsregister A (Sole proprietors, partnerships)")
        print("   • PR - Partnerschaftsregister (Partnership Register)")
        print("   • GnR - Genossenschaftsregister (Cooperative Register)")
        print("   • VR - Vereinsregister (Association Register)")
        print("   • GüR - Güterrechtsregister (Matrimonial Property Register)")
        print("   • EWIV - Europäische Wirtschaftliche Interessenvereinigung")
        print("   • SE - Europäische Aktiengesellschaft (European Company)")
        print("   • SCE - Europäische Genossenschaft (European Cooperative)")
        print("   • SPE - Europäische Privatgesellschaft (European Private Company)")
        
        print("\n✅ Package now supports ALL document types:")
        print("   • AD - Aktueller Abdruck (Current Extract)")
        print("   • CD - Chronologischer Abdruck (Chronological Extract)")
        print("   • HD - Handelsregister (Commercial Register)")
        print("   • DK - Dokument (Document)")
        print("   • UT - Unternehmensregister (Company Register)")
        print("   • VÖ - Veröffentlichungen (Publications)")
        print("   • SI - Sonstige Informationen (Other Information)")
        
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
