#!/usr/bin/env python3
"""
Lead Enrichment Pipeline
Combines PDF scraping with automatic data extraction
"""

import asyncio
import os
import sys
from pathlib import Path
from pdf_extractor import PDFTableExtractor

# Import the working scraper
from scraper_working import search_and_download as run_scraper

class LeadEnrichmentPipeline:
    """
    Pipeline that combines PDF scraping with automatic data extraction
    """
    
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.extracted_dir = Path("extracted_tables")
        self.enriched_dir = Path("enriched_data")
        
        # Create necessary directories
        self.downloads_dir.mkdir(exist_ok=True)
        self.extracted_dir.mkdir(exist_ok=True)
        self.enriched_dir.mkdir(exist_ok=True)
    
    async def run_scraping_phase(self, company_name: str):
        """
        Phase 1: Run the PDF scraper to download documents
        
        Args:
            company_name (str): Company name to search for
        """
        print("🚀 PHASE 1: Starting PDF Scraping")
        print("=" * 50)
        
        try:
            # Run the working scraper
            await run_scraper(company_name)
            print("✅ Scraping phase completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during scraping phase: {e}")
            raise
    
    def run_extraction_phase(self):
        """
        Phase 2: Extract data from downloaded PDFs
        """
        print("\n🔍 PHASE 2: Starting PDF Data Extraction")
        print("=" * 50)
        
        try:
            # Initialize the PDF extractor
            extractor = PDFTableExtractor()
            
            # Process all downloaded PDFs
            generated_files = extractor.process_all_pdfs()
            
            if generated_files:
                print(f"✅ Extraction phase completed! Generated {len(generated_files)} markdown files")
                return generated_files
            else:
                print("⚠️  No PDFs were processed during extraction phase")
                return []
                
        except Exception as e:
            print(f"❌ Error during extraction phase: {e}")
            raise
    
    def run_enrichment_phase(self, extracted_files: list):
        """
        Phase 3: Process and enrich the extracted data
        
        Args:
            extracted_files (list): List of extracted markdown files
        """
        print("\n🎯 PHASE 3: Starting Data Enrichment")
        print("=" * 50)
        
        try:
            enriched_count = 0
            
            for file_path in extracted_files:
                print(f"📄 Processing: {Path(file_path).name}")
                
                # Read the extracted markdown content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create enriched version with additional processing
                enriched_content = self._enrich_content(content, Path(file_path).name)
                
                # Save enriched content
                enriched_filename = f"enriched_{Path(file_path).name}"
                enriched_path = self.enriched_dir / enriched_filename
                
                with open(enriched_path, 'w', encoding='utf-8') as f:
                    f.write(enriched_content)
                
                print(f"   💾 Saved enriched data: {enriched_filename}")
                enriched_count += 1
            
            print(f"✅ Enrichment phase completed! Processed {enriched_count} files")
            return enriched_count
            
        except Exception as e:
            print(f"❌ Error during enrichment phase: {e}")
            raise
    
    def _enrich_content(self, content: str, filename: str) -> str:
        """
        Enrich the extracted content with additional processing
        
        Args:
            content (str): Original extracted content
            filename (str): Name of the source file
            
        Returns:
            str: Enriched content
        """
        # Add enrichment header
        enriched = f"# Enriched Data from: {filename}\n\n"
        enriched += f"**Processing Date**: {os.popen('date').read().strip()}\n\n"
        enriched += "---\n\n"
        
        # Add original content
        enriched += content
        
        # Add summary section
        enriched += "\n\n---\n\n"
        enriched += "## Data Summary\n\n"
        
        # Count tables and text sections
        table_count = content.count("### Table")
        text_count = content.count("### Page")
        
        enriched += f"- **Total Tables Extracted**: {table_count}\n"
        enriched += f"- **Total Text Sections**: {text_count}\n"
        enriched += f"- **Source File**: {filename}\n"
        enriched += f"- **Processing Status**: ✅ Completed\n"
        
        return enriched
    
    async def run_full_pipeline(self, company_name: str):
        """
        Run the complete pipeline: Scraping → Extraction → Enrichment
        
        Args:
            company_name (str): Company name to search for
        """
        print("🎉 LEAD ENRICHMENT PIPELINE STARTING")
        print("=" * 60)
        print(f"🎯 Target Company: {company_name}")
        print("=" * 60)
        
        try:
            # Phase 1: Scraping
            await self.run_scraping_phase(company_name)
            
            # Check if any PDFs were downloaded
            pdf_files = list(self.downloads_dir.glob("*.pdf"))
            if not pdf_files:
                print("⚠️  No PDFs were downloaded. Skipping extraction and enrichment phases.")
                return
            
            print(f"📁 Found {len(pdf_files)} downloaded PDFs")
            
            # Phase 2: Extraction
            extracted_files = self.run_extraction_phase()
            
            if not extracted_files:
                print("⚠️  No data was extracted. Skipping enrichment phase.")
                return
            
            # Phase 3: Enrichment
            enriched_count = self.run_enrichment_phase(extracted_files)
            
            # Final summary
            print("\n" + "=" * 60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"📥 Downloaded PDFs: {len(pdf_files)}")
            print(f"🔍 Extracted Files: {len(extracted_files)}")
            print(f"🎯 Enriched Files: {enriched_count}")
            print(f"📁 Output Locations:")
            print(f"   - Downloads: {self.downloads_dir}")
            print(f"   - Extracted: {self.extracted_dir}")
            print(f"   - Enriched: {self.enriched_dir}")
            
        except Exception as e:
            print(f"\n❌ PIPELINE FAILED: {e}")
            print("=" * 60)
            raise

async def main():
    """
    Main function to run the pipeline
    """
    if len(sys.argv) != 2:
        print("Usage: python pipeline.py 'Company Name'")
        print("Example: python pipeline.py 'Competence Call Center'")
        sys.exit(1)
    
    company_name = sys.argv[1]
    
    # Initialize and run the pipeline
    pipeline = LeadEnrichmentPipeline()
    await pipeline.run_full_pipeline(company_name)

if __name__ == "__main__":
    # Run the async pipeline
    asyncio.run(main())
