#!/usr/bin/env python3
"""
Production configuration for Lead Enrichment Pipeline
"""

# Directory Configuration
DOWNLOADS_DIR = "downloads"
OUTPUT_DIR = "enriched_data"
TEMP_DIR = "temp"

# Scraping Configuration
SCRAPER_TIMEOUT = 30000  # milliseconds
DOWNLOAD_DELAY = 3000    # milliseconds between downloads
COMPANY_DELAY = 10       # seconds between companies

# PDF Processing Configuration
MAX_PDF_SIZE_MB = 100    # Maximum PDF size to process
SUPPORTED_PDF_TYPES = ['.pdf']

# Output Configuration
MARKDOWN_EXTENSION = '.md'
INCLUDE_METADATA = True
INCLUDE_TEXT_CONTENT = True
INCLUDE_TABLES = True

# Error Handling
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Performance Configuration
MAX_CONCURRENT_PDFS = 1  # Process PDFs sequentially for stability
BATCH_SIZE = 5           # Process companies in batches
