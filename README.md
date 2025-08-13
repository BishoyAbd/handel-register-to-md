# Scraper Library

A modular Python package containing production-ready web scrapers. It currently ships with the German Handelsregister (Commercial Register) scraper.

## Features

- Headless, Playwright-based browser automation
- In-memory data interface (no forced file I/O)
- Extracts PDFs and Markdown from official documents
- Enum-based document filtering (AD, CD)
- Enhanced registration number matching with LCS algorithm
- Robust error signaling with retry recommendations
- CLI and programmatic APIs

## Quick Start

### 1) Install (uv recommended)

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install the package (editable for local development)
uv pip install -e .

# Install Playwright browser binaries
playwright install chromium
```

Alternatively with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

### 2) Command Line Usage

```bash
# Download all available documents (AD and CD)
hr-scraper "Company Name GmbH"

# With registration number (HRB) for precise matching
hr-scraper "Company Name GmbH" --registration-number "HRB 12345"
hr-scraper "Company Name GmbH" --registration-number "123 456"
hr-scraper "Company Name GmbH" --registration-number "123456A"

# Download specific document types
hr-scraper "Company Name GmbH" --document-types AD
hr-scraper "Company Name GmbH" --document-types CD
hr-scraper "Company Name GmbH" --document-types AD CD

# Show JSON output for programmatic consumption
hr-scraper "Company Name GmbH" --json

# Save PDFs and Markdown to disk (demo helper)
hr-scraper "Company Name GmbH" --output-dir output
```

### 3) Programmatic Usage

```python
import asyncio
from scraper.hr_scraper import ScraperApp, DocumentType

async def main():
    app = ScraperApp(headless=True)

    # Download only AD with registration number
    result = await app.run(
        "Adler Real Estate GmbH", 
        registration_number="259502",
        document_types=[DocumentType.AD]
    )

    # Download only CD
    # result = await app.run("Adler Real Estate GmbH", document_types=[DocumentType.CD])

    # Download both AD and CD
    # result = await app.run("Adler Real Estate GmbH", document_types=[DocumentType.AD, DocumentType.CD])

    if result["success"]:
        print("Company:", result["company_info"])
        for doc in result["documents"]:
            pdf_bytes = doc["pdf_content"]
            md_text = doc["markdown_content"]
            # Process data as needed
    else:
        print("Error:", result["error"])

asyncio.run(main())
```

## Enhanced Registration Number Matching

The scraper now supports intelligent registration number matching using the Longest Common Subsequence (LCS) algorithm:

- **Flexible Input Formats**: Accepts various HRB formats:
  - `259502` (clean number)
  - `259 502` (with spaces)
  - `HRB 259502` (with prefix)
  - `HRB: 259502` (with colon)
  - `259502A` (with letter suffix)
  - `HRB 259 502 A` (complex format)

- **Smart Similarity Scoring**: Provides similarity scores (0.0-1.0) for registration numbers
- **Fallback Matching**: Gracefully falls back to name-only matching when registration parsing fails
- **Precise Company Identification**: Registration numbers significantly improve matching accuracy

## Document Type Filtering

- `DocumentType.AD`: Aktueller Abdruck (Current Extract)
- `DocumentType.CD`: Chronologischer Abdruck (Chronological Extract)

If no document types are specified, all available documents are downloaded.

## Return Structure

The `ScraperApp.run(...)` method returns a dictionary:

```python
{
  "success": bool,
  "error": str | None,
  "retry_recommended": bool,
  "company_info": { "name": str, "hrb": str, "search_query": str } | None,
  "documents": [
    {
      "doc_type": "AD" | "CD",
      "pdf_content": bytes,
      "pdf_filename": str,
      "markdown_content": str,
      "markdown_filename": str,
    },
    ...
  ],
  "debug_info": dict
}
```

## Dependencies

- Playwright (>= 1.54)
- pdfplumber (>= 0.11.7)
- aiofiles (>= 24.1.0)

Install exact versions from `requirements.txt` or let pip/uv resolve from `pyproject.toml`.

## Development

```bash
# Run test client (examples of AD/CD filtering)
python test_client_documents.py

# Test enhanced registration number matching
python test_registration_matching.py
```

## Versioning & Distribution

- Project metadata and dependencies are defined in `pyproject.toml`
- For local usage: `pip/uv install -e .`
- For publishing, configure your remote repository and CI to build wheels/sdist
