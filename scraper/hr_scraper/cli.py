#!/usr/bin/env python3
"""
Command-line interface for the HR Scraper.

This module provides the CLI entry point for the scraper package.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .app import ScraperApp
from .models import DocumentType
from .logger import get_logger

logger = get_logger(__name__)

def save_documents_to_files(result, output_dir: str = "client_output"):
    """Helper function to demonstrate how a client might save the returned data"""
    if not result.get('success') or not result.get('documents'):
        print("No documents to save.")
        return
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    company_name = result['company_info']['name']
    company_dir = output_path / f"{company_name}_{result['company_info']['hrb']}"
    company_dir.mkdir(exist_ok=True)
    
    print(f"\nSaving documents to: {company_dir}")
    
    for doc in result['documents']:
        # Save PDF
        pdf_path = company_dir / doc['pdf_filename']
        with open(pdf_path, 'wb') as f:
            f.write(doc['pdf_content'])
        print(f"  Saved PDF: {pdf_path}")
        
        # Save Markdown
        md_path = company_dir / doc['markdown_filename']
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(doc['markdown_content'])
        print(f"  Saved Markdown: {md_path}")

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Scrape company documents from Handelsregister.")
    parser.add_argument('company_name', help='Name of the company to search for')
    parser.add_argument('--document-types', '-t', nargs='+', 
                       choices=['AD', 'CD', 'HD', 'DK', 'UT', 'VÖ', 'SI'], 
                       help='Document types to download (AD, CD, HD, DK, UT, VÖ, SI, or any combination). If not specified, downloads all available.')
    parser.add_argument('--registration-number', '-r', 
                       help='Optional registration number for more precise matching. Supports all German formats: HRB, HRA, PR, GnR, VR, GüR, EWIV, SE, SCE, SPE, etc.')
    parser.add_argument('--output-dir', '-o', default='.', help='Output directory for saving files (default: current directory)')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode (default: True)')
    args = parser.parse_args()

    # Convert document types to enum if specified
    document_types = None
    if args.document_types:
        document_types = [DocumentType(dt) for dt in args.document_types]

    # Default to headless=True, unless --show-browser is passed
    app = ScraperApp(headless=not args.headless)
    
    try:
        # Run the scraper
        result = await app.run(
            company_name=args.company_name,
            registration_number=args.registration_number,
            document_types=document_types
        )
        
        if args.json:
            # Output JSON format for programmatic use
            print(json.dumps(result, indent=2))
            return
        
        # Display results in human-readable format
        print("\n" + "="*60)
        print("SCRAPER RESULTS")
        print("="*60)
        
        if result['success']:
            print(f"✅ SUCCESS: Found {len(result['documents'])} documents")
            print(f"Company: {result['company_info']['name']}")
            print(f"HRB: {result['company_info']['hrb']}")
            
            print(f"\nDocuments found:")
            for i, doc in enumerate(result['documents'], 1):
                print(f"  {i}. {doc['doc_type']} - {doc['pdf_filename']}")
                print(f"     PDF size: {len(doc['pdf_content'])} bytes")
                print(f"     Markdown preview: {doc['markdown_content'][:100]}...")
            
            # Demonstrate saving files if requested
            if args.output_dir != '.': # Only save if output_dir is not default
                save_documents_to_files(result, args.output_dir)
                
        else:
            print(f"❌ FAILED: {result['error']}")
            print(f"Retry recommended: {'Yes' if result['retry_recommended'] else 'No'}")
            
            if result.get('debug_info'):
                print(f"\nDebug information:")
                for key, value in result['debug_info'].items():
                    print(f"  {key}: {value}")
        
        # Show the complete result structure for client reference
        print(f"\n" + "="*60)
        print("COMPLETE RESULT STRUCTURE")
        print("="*60)
        print("The scraper returns a dictionary with the following structure:")
        print(json.dumps({
            'success': result['success'],
            'error': result['error'],
            'retry_recommended': result['retry_recommended'],
            'company_info': result['company_info'],
            'documents_count': len(result['documents']),
            'debug_info_keys': list(result['debug_info'].keys()) if result['debug_info'] else []
        }, indent=2))
        
        print(f"\n" + "="*60)
        print("CLIENT USAGE EXAMPLE")
        print("="*60)
        print("""
# Programmatic usage example:
from scraper.hr_scraper import ScraperApp, DocumentType

# Download only AD documents
app = ScraperApp(headless=True)
result = await app.run("Company Name GmbH", document_types=[DocumentType.AD])

# Download only CD documents
result = await app.run("Company Name GmbH", document_types=[DocumentType.CD])

# Download both AD and CD documents
result = await app.run("Company Name GmbH", document_types=[DocumentType.AD, DocumentType.CD])

# Download all available documents (default)
result = await app.run("Company Name GmbH")

if result['success']:
    for doc in result['documents']:
        pdf_bytes = doc['pdf_content']          # PDF as bytes
        markdown_text = doc['markdown_content'] # Markdown as string
        
        # Do whatever you want with the data:
        # - Save to database
        # - Upload to cloud storage
        # - Process with NLP tools
        # - Send via API
        # - etc.
else:
    if result['retry_recommended']:
        print(f"Error: {result['error']} - Consider retrying")
    else:
        print(f"Error: {result['error']} - Do not retry")
""")
            
    except Exception as e:
        logger.critical(f"An unexpected error occurred in main: {e}", exc_info=True)
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("Check the logs for more details.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
