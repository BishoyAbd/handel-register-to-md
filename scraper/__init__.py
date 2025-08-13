"""
Scraper Package - Collection of web scrapers.

This package contains various web scrapers for different purposes:
- hr_scraper: German Handelsregister (Commercial Register) scraper
- (future scrapers can be added here)

Usage:
    from scraper.hr_scraper import ScraperApp
    from scraper.hr_scraper import scrape_company
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# Import main components from hr_scraper for easy access
from .hr_scraper.app import ScraperApp
from .hr_scraper.models import Company, Document, EnrichedCompany, DocumentType
from .hr_scraper.exceptions import ScraperException, CompanyNotFoundError

__all__ = [
    "ScraperApp",
    "Company",
    "Document", 
    "EnrichedCompany",
    "DocumentType",
    "ScraperException",
    "CompanyNotFoundError",
]
