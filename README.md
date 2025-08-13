# Scraper Library

A modular Python package containing production-ready web scrapers. It currently ships with the German Handelsregister (Commercial Register) scraper.

## Features

- Headless, Playwright-based browser automation
- In-memory data interface (no forced file I/O)
- Extracts PDFs and Markdown from official documents
- Enum-based document filtering (AD, CD)
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

# With registration number (HRB)
hr-scraper "Company Name GmbH" "HRB 12345"

# Download specific document types
hr-scraper "Company Name GmbH" --document-types AD
hr-scraper "Company Name GmbH" --document-types CD
hr-scraper "Company Name GmbH" --document-types AD CD

# Show JSON output for programmatic consumption
hr-scraper "Company Name GmbH" --json

# Save PDFs and Markdown to disk (demo helper)
hr-scraper "Company Name GmbH" --save-files --output-dir output
```

### 3) Programmatic Usage

```python
import asyncio
from scraper.hr_scraper import ScraperApp, DocumentType

async def main():
    app = ScraperApp(headless=True)

    # Download only AD
    result = await app.run("Adler Real Estate GmbH", document_types=[DocumentType.AD])

    # Download only CD
    # result = await app.run("Adler Real Estate GmbH", document_types=[DocumentType.CD])

    # Download both AD and CD
    # result = await app.run("Adler Real Estate GmbH", document_types=[DocumentType.AD, DocumentType.CD])

    if result["success"]:
        print("Company:", result["company_info"])  # { name, hrb, search_query }
        for doc in result["documents"]:
            pdf_bytes = doc["pdf_content"]
            md_text = doc["markdown_content"]
            # Do whatever you want (DB, storage, APIs, analytics, etc.)
    else:
        print("Error:", result["error"])  # decide based on retry_recommended

asyncio.run(main())
```

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

- Use `success` and `retry_recommended` to implement robust retry logic
- PDFs are returned as bytes, Markdown as strings — you control persistence

## Dependencies

- Playwright (>= 1.54)
- pdfplumber (>= 0.11.7)
- aiofiles (>= 24.1.0)

Install exact versions from `requirements.txt` or let pip/uv resolve from `pyproject.toml`.

## Troubleshooting

- Run `playwright install chromium` once per environment
- Increase timeouts in `scraper/hr_scraper/config.py` for slow networks
- Use `--json` to inspect detailed results
- Check `debug_info` when failures occur

## Development

```bash
# Lint/format/type-check (if you installed optional dev extras)
black scraper/
isort scraper/
mypy scraper/

# Run test client (examples of AD/CD filtering)
python test_client_documents.py
```

## Versioning & Distribution

- Project metadata and dependencies are defined in `pyproject.toml`
- For local usage: `pip/uv install -e .`
- For publishing, configure your remote repository and CI to build wheels/sdist
