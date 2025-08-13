# HR Scraper - Client Usage Guide

This scraper extracts company documents from the German Handelsregister (Commercial Register) website and returns the data directly to the client instead of saving files locally.

## Key Changes from Previous Version

- **No local file saving**: The scraper no longer saves files to the `downloads/` directory
- **Data returned in memory**: PDF content and markdown are returned as bytes/strings
- **Better error handling**: Clear indication of whether retry is recommended
- **Client control**: Clients decide what to do with the returned data

## Basic Usage

### Command Line Interface

```bash
# Basic scraping
python -m scraper.hr_scraper.main "Company Name GmbH"

# With registration number
python -m scraper.hr_scraper.main "Company Name GmbH" "HRB 12345"

# Show browser (for debugging)
python -m scraper.hr_scraper.main "Company Name GmbH" --show-browser

# Save files (demonstration)
python -m scraper.hr_scraper.main "Company Name GmbH" --save-files --output-dir my_output
```

### Programmatic Usage

```python
import asyncio
from scraper.hr_scraper.app import ScraperApp

async def scrape_company():
    app = ScraperApp(headless=True)
    result = await app.run("Company Name GmbH", "HRB 12345")
    
    if result['success']:
        # Access company information
        company_name = result['company_info']['name']
        company_hrb = result['company_info']['hrb']
        
        # Process each document
        for doc in result['documents']:
            pdf_bytes = doc['pdf_content']          # PDF as bytes
            markdown_text = doc['markdown_content'] # Markdown as string
            
            # Do whatever you want with the data
            # - Save to database
            # - Upload to cloud storage
            # - Process with NLP tools
            # - Send via API
            # - Save to custom location
    else:
        if result['retry_recommended']:
            print(f"Error: {result['error']} - Consider retrying")
        else:
            print(f"Error: {result['error']} - Do not retry")

# Run the async function
asyncio.run(scrape_company())
```

## Return Data Structure

The scraper returns a dictionary with the following structure:

```python
{
    'success': bool,                    # Whether scraping was successful
    'error': str or None,               # Error message if failed
    'retry_recommended': bool,          # Whether retry is recommended
    'company_info': {                   # Company details (if found)
        'name': str,                    # Company name
        'hrb': str,                     # Registration number
        'search_query': str             # Original search query
    },
    'documents': [                      # List of documents (if found)
        {
            'doc_type': str,            # Document type (AD, CD)
            'pdf_content': bytes,       # PDF file content as bytes
            'pdf_filename': str,        # Suggested filename for PDF
            'markdown_content': str,    # Extracted content as markdown
            'markdown_filename': str    # Suggested filename for markdown
        }
    ],
    'debug_info': {                     # Debug information for troubleshooting
        'screenshot_saved': bool,       # Whether debug screenshots were saved
        'html_saved': bool,             # Whether debug HTML was saved
        'ui_messages': list,            # UI messages from the website
        'document_errors': list,        # Errors during document processing
        'error_screenshot_saved': bool  # Whether error screenshots were saved
    }
}
```

## Error Handling

### Retry Recommendations

The `retry_recommended` field helps clients decide whether to retry:

- **`True`**: Retry might help (network issues, temporary website problems)
- **`False`**: Retry won't help (company doesn't exist, invalid input)

### Common Error Scenarios

```python
result = await app.run("Company Name")

if not result['success']:
    if result['retry_recommended']:
        # These errors suggest retry might help:
        # - "No companies found on the results page"
        # - "No documents found for company"
        # - Network timeouts, connection issues
        print("Temporary issue - retry later")
    else:
        # These errors suggest no retry will help:
        # - "No suitable company match found"
        # - "Cannot process company without registration number"
        print("Permanent issue - don't retry")
```

## Examples

See `client_example.py` for comprehensive examples including:

- Basic usage
- Custom file saving
- Database integration
- Error handling
- Batch processing

## Configuration

The scraper uses the following configuration (see `config.py`):

- **Timeouts**: Configurable timeouts for navigation and downloads
- **User Agent**: Customizable browser user agent
- **Selectors**: CSS selectors for website elements

## Dependencies

Required packages (see `requirements.txt`):
- `playwright`: Browser automation
- `pdfplumber`: PDF text extraction
- Standard Python libraries

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Troubleshooting

### Debug Information

When errors occur, the scraper saves debug information:

- Screenshots of the current page
- HTML content for inspection
- UI messages from the website

### Common Issues

1. **No companies found**: Check company name spelling, try variations
2. **No documents found**: Company might not have public documents
3. **Browser errors**: Ensure Playwright is properly installed
4. **Timeout errors**: Network issues, increase timeout values in config

## Client Responsibilities

With the refactored scraper, clients are responsible for:

- **Data storage**: Saving PDFs and markdown where needed
- **Error handling**: Implementing retry logic based on recommendations
- **Resource management**: Handling large PDF files in memory
- **Rate limiting**: Implementing delays between requests if needed
- **Data processing**: Converting markdown to other formats if required

## Performance Notes

- **Memory usage**: PDF content is held in memory, consider for large files
- **Network**: Each request involves web scraping, implement appropriate delays
- **Concurrency**: The scraper is async-ready for concurrent processing
