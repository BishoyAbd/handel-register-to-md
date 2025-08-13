"""
HR Scraper - German Handelsregister (Commercial Register) scraper.

This subpackage provides functionality to scrape company documents from the German
commercial register and return them as structured data.

Main components:
- ScraperApp: Main application class for scraping companies
- DocumentType: Enum for document types (AD, CD)
- scrape_company: Convenience function for one-off scraping
"""

from .app import ScraperApp
from .models import Company, Document, EnrichedCompany, DocumentType
from .exceptions import ScraperException, CompanyNotFoundError

__all__ = [
    "ScraperApp",
    "Company",
    "Document", 
    "EnrichedCompany",
    "DocumentType",
    "ScraperException",
    "CompanyNotFoundError",
]
