#!/usr/bin/env python3
"""
Test script for HRA company registration type.
"""

import asyncio
import sys
from pathlib import Path

# Add the scraper package to the path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.hr_scraper import ScraperApp, DocumentType

async def test_hra_company():
    """Test HRA company registration type."""
    
    print("🔍 Testing HRA Company Registration Type")
    print("=" * 50)
    print("Company: Bode Projects e. k.")
    print("Registration: HRA 57863 B")
    print("-" * 50)
    
    app = ScraperApp(headless=True)
    
    try:
        # Try AD first
        print("🔍 Trying AD documents...")
        result = await app.run(
            company_name="Bode Projects e. k.",
            registration_number="HRA 57863 B",
            document_types=[DocumentType.AD]
        )
        
        if result['success']:
            print(f"✅ Success! Matched company: {result['company_info']['name']}")
            print(f"   Registration: {result['company_info']['hrb']}")
            print(f"   Documents found: {len(result['documents'])}")
        else:
            print(f"❌ AD failed: {result['error']}")
            
            # Try CD documents
            print("\n🔍 Trying CD documents...")
            result = await app.run(
                company_name="Bode Projects e. k.",
                registration_number="HRA 57863 B",
                document_types=[DocumentType.CD]
            )
            
            if result['success']:
                print(f"✅ Success! Matched company: {result['company_info']['name']}")
                print(f"   Registration: {result['company_info']['hrb']}")
                print(f"   Documents found: {len(result['documents'])}")
            else:
                print(f"❌ CD also failed: {result['error']}")
                
                # Try all document types
                print("\n🔍 Trying all document types...")
                result = await app.run(
                    company_name="Bode Projects e. k.",
                    registration_number="HRA 57863 B"
                )
                
                if result['success']:
                    print(f"✅ Success! Matched company: {result['company_info']['name']}")
                    print(f"   Registration: {result['company_info']['hrb']}")
                    print(f"   Documents found: {len(result['documents'])}")
                else:
                    print(f"❌ All types failed: {result['error']}")
                    
    except Exception as e:
        print(f"💥 Exception: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(test_hra_company())
