# Scraper Package

A collection of web scrapers for various purposes, built with modern Python and async support.

## Current Scrapers

### HR Scraper (`scraper.hr_scraper`)
German Handelsregister (Commercial Register) scraper that extracts company documents and returns them as structured data.

## Installation

### Using uv (Recommended)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode
uv pip install -e .
```

### Using pip
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

## Usage

### HR Scraper

#### Command Line
```bash
# Basic usage
hr-scraper "Company Name GmbH"

# With registration number
hr-scraper "Company Name GmbH" "HRB 12345"

# Show browser (for debugging)
hr-scraper "Company Name GmbH" --show-browser

# Output JSON format
hr-scraper "Company Name GmbH" --json

# Save files (demonstration)
hr-scraper "Company Name GmbH" --save-files --output-dir my_output
```

#### Programmatic Usage
```python
import asyncio
from scraper.hr_scraper import ScraperApp

async def main():
    app = ScraperApp(headless=True)
    result = await app.run("Company Name GmbH", "HRB 12345")
    
    if result['success']:
        print(f"Found {len(result['documents'])} documents")
        for doc in result['documents']:
            pdf_bytes = doc['pdf_content']          # PDF as bytes
            markdown_text = doc['markdown_content'] # Markdown as string
            
            # Do whatever you want with the data
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

# Run the async function
asyncio.run(main())
```

#### Simple Import
```python
# Import main components directly
from scraper import ScraperApp, Company, Document

# Or import from specific scraper
from scraper.hr_scraper import ScraperApp
```

## Package Structure

```
scraper/
├── __init__.py              # Main package init
├── hr_scraper/              # HR Scraper subpackage
│   ├── __init__.py
│   ├── app.py               # Main ScraperApp class
│   ├── browser_manager.py   # Browser management
│   ├── company_matcher.py   # Company matching logic
│   ├── config.py            # Configuration
│   ├── data_extractor.py    # Data extraction
│   ├── exceptions.py        # Custom exceptions
│   ├── file_manager.py      # File operations
│   ├── logger.py            # Logging
│   ├── main.py              # CLI entry point
│   ├── models.py            # Data models
│   ├── navigator.py         # Web navigation
│   ├── pdf_extractor.py     # PDF processing
│   └── cli.py               # Command-line interface
└── README.md                # This file
```

## Adding New Scrapers

To add a new scraper:

1. Create a new subpackage in the `scraper/` directory
2. Follow the same structure as `hr_scraper/`
3. Update the main `scraper/__init__.py` to expose the new scraper
4. Add any new dependencies to `pyproject.toml`

Example structure for a new scraper:
```
scraper/
├── hr_scraper/              # Existing HR scraper
├── new_scraper/             # New scraper
│   ├── __init__.py
│   ├── app.py
│   └── ...
└── __init__.py              # Expose both scrapers
```

## Development

### Setup Development Environment
```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks (if configured)
pre-commit install
```

### Running Tests
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=scraper
```

### Code Quality
```bash
# Format code
black scraper/

# Sort imports
isort scraper/

# Type checking
mypy scraper/
```

## Dependencies

- **playwright**: Browser automation
- **pdfplumber**: PDF text extraction
- **aiofiles**: Async file operations

## License

MIT License - see LICENSE file for details.
