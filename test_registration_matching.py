#!/usr/bin/env python3
"""
Test script for enhanced registration number matching.
Demonstrates the LCS algorithm and smart HRB parsing.
"""

import asyncio
import sys
from pathlib import Path

# Add the scraper package to the path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.hr_scraper import ScraperApp, DocumentType

async def test_registration_matching():
    """Test various registration number formats and matching scenarios."""
    
    print("🔍 Enhanced Registration Number Matching Test")
    print("=" * 60)
    
    # Test cases with different registration number formats
    test_cases = [
        {
            'name': 'Adler Real Estate GmbH',
            'registration': '259502',
            'description': 'Clean number without spaces'
        },
        {
            'name': 'Adler Real Estate GmbH',
            'registration': '259 502',
            'description': 'Number with spaces'
        },
        {
            'name': 'Adler Real Estate GmbH',
            'registration': 'HRB 259502',
            'description': 'With HRB prefix'
        },
        {
            'name': 'Adler Real Estate GmbH',
            'registration': 'HRB: 259502',
            'description': 'With HRB: prefix'
        },
        {
            'name': 'Adler Real Estate GmbH',
            'registration': 'HRB 259 502',
            'description': 'HRB prefix with spaces'
        },
        {
            'name': 'Adler Real Estate GmbH',
            'registration': '259502A',
            'description': 'Number with letter suffix'
        },
        {
            'name': 'Adler Real Estate GmbH',
            'registration': 'HRB 259 502 A',
            'description': 'HRB prefix, spaces, and letter'
        },
        {
            'name': 'Adler Real Estate GmbH',
            'registration': None,
            'description': 'No registration number (name-only matching)'
        }
    ]
    
    app = ScraperApp(headless=True)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print(f"   Company: {test_case['name']}")
        print(f"   Registration: {test_case['registration']}")
        print("-" * 50)
        
        try:
            result = await app.run(
                company_name=test_case['name'],
                registration_number=test_case['registration'],
                document_types=[DocumentType.AD]  # Just test with AD for speed
            )
            
            if result['success']:
                print(f"✅ Success! Matched company: {result['company_info']['name']}")
                print(f"   HRB: {result['company_info']['hrb']}")
                print(f"   Documents found: {len(result['documents'])}")
                
                # Show registration number similarity if both exist
                if test_case['registration'] and result['company_info']['hrb']:
                    from scraper.hr_scraper.company_matcher import CompanyMatcher
                    matcher = CompanyMatcher()
                    similarity = matcher._calculate_registration_similarity(
                        test_case['registration'], 
                        result['company_info']['hrb']
                    )
                    print(f"   Registration similarity: {similarity:.3f}")
            else:
                print(f"❌ Failed: {result['error']}")
                if result.get('retry_recommended'):
                    print("   Consider retrying this request")
                    
        except Exception as e:
            print(f"💥 Exception: {e}")
        
        print()
    
    print("=" * 60)
    print("🎯 Key Benefits of Enhanced Registration Matching:")
    print("1. Handles various HRB formats (spaces, prefixes, suffixes)")
    print("2. Uses Longest Common Subsequence algorithm for fuzzy matching")
    print("3. Provides similarity scores for registration numbers")
    print("4. Falls back to name-only matching when no registration provided")
    print("5. Smart normalization of input formats")

if __name__ == "__main__":
    asyncio.run(test_registration_matching())
