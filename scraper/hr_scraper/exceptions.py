class ScraperException(Exception):
    """Base exception for the scraper application."""
    pass

class NavigationError(ScraperException):
    """Raised when navigation to a page fails."""
    pass

class NoResultsFoundError(ScraperException):
    """Raised when a search yields no results."""
    pass

class DownloadFailedError(ScraperException):
    """Raised when a document download fails."""
    pass

class CompanyNotFoundError(ScraperException):
    """Raised when no matching company is found."""
    pass
