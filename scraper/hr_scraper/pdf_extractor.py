import pdfplumber
import pathlib
import re
import io
from typing import List, Dict, Any, Union

from .logger import get_logger

logger = get_logger(__name__)

class PDFExtractor:
    """A component to extract tables and text from a PDF file and format as markdown."""

    def extract_content_as_markdown(self, pdf_path: Union[str, pathlib.Path]) -> str:
        """
        Extracts all tables and text from a given PDF file and returns them
        as a single markdown-formatted string.

        Args:
            pdf_path: The path to the PDF file (string or Path object).

        Returns:
            A string containing the extracted data in markdown format.
        """
        # Convert string to Path if needed
        if isinstance(pdf_path, str):
            pdf_path = pathlib.Path(pdf_path)
            
        logger.info(f"Extracting content from: {pdf_path.name}")
        extracted_data = self._extract_data(pdf_path)
        markdown_content = self._format_as_markdown(extracted_data)
        return markdown_content

    def extract_content_from_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> str:
        """
        Extracts all tables and text from PDF bytes in memory and returns them
        as a single markdown-formatted string.

        Args:
            pdf_bytes: PDF content as bytes.
            filename: Name of the file for logging purposes.

        Returns:
            A string containing the extracted data in markdown format.
        """
        logger.info(f"Extracting content from bytes: {filename}")
        extracted_data = self._extract_data_from_bytes(pdf_bytes, filename)
        markdown_content = self._format_as_markdown(extracted_data)
        return markdown_content

    def _extract_data_from_bytes(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Core data extraction logic using pdfplumber from bytes."""
        data = {'filename': filename, 'tables': [], 'text_content': [], 'metadata': {}}
        try:
            # Create a BytesIO object from the bytes
            pdf_stream = io.BytesIO(pdf_bytes)
            
            with pdfplumber.open(pdf_stream) as pdf:
                data['metadata'] = {
                    'pages': len(pdf.pages),
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                }
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    if tables:
                        for table_num, table in enumerate(tables):
                            if table and any(any(cell for cell in row if cell) for row in table):
                                data['tables'].append({
                                    'page': page_num + 1,
                                    'table_number': table_num + 1,
                                    'data': table
                                })
                    text = page.extract_text()
                    if text and text.strip():
                        data['text_content'].append({'page': page_num + 1, 'text': text.strip()})
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            data['error'] = str(e)
        return data

    def _extract_data(self, pdf_path: pathlib.Path) -> Dict[str, Any]:
        """Core data extraction logic using pdfplumber."""
        data = {'filename': pdf_path.name, 'tables': [], 'text_content': [], 'metadata': {}}
        try:
            with pdfplumber.open(pdf_path) as pdf:
                data['metadata'] = {
                    'pages': len(pdf.pages),
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                }
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    if tables:
                        for table_num, table in enumerate(tables):
                            if table and any(any(cell for cell in row if cell) for row in table):
                                data['tables'].append({
                                    'page': page_num + 1,
                                    'table_number': table_num + 1,
                                    'data': table
                                })
                    text = page.extract_text()
                    if text and text.strip():
                        data['text_content'].append({'page': page_num + 1, 'text': text.strip()})
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
            data['error'] = str(e)
        return data

    def _format_as_markdown(self, extracted_data: Dict[str, Any]) -> str:
        """Converts the extracted data dictionary into a markdown string."""
        content = [f"# Extracted Data from: {extracted_data['filename']}\n"]
        if extracted_data['metadata']:
            content.append("## Document Metadata\n")
            for key, value in extracted_data['metadata'].items():
                content.append(f"- **{key.title()}**: {value}")
            content.append("\n")
        
        if extracted_data['tables']:
            content.append("## Extracted Tables\n")
            for table_info in extracted_data['tables']:
                content.append(f"### Table {table_info['table_number']} (Page {table_info['page']})\n")
                content.append(self._table_to_markdown(table_info['data']))
                content.append("\n")

        if extracted_data['text_content']:
            content.append("## Extracted Text Content\n")
            for text_section in extracted_data['text_content']:
                content.append(f"### Page {text_section['page']}\n")
                content.append(f"```\n{text_section['text']}\n```\n")

        if 'error' in extracted_data:
            content.append("## Errors\n")
            content.append(f"❌ {extracted_data['error']}")

        return "\n".join(content)

    def _table_to_markdown(self, table: List[List[str]]) -> str:
        """Converts a list of lists into a markdown table."""
        if not table or not table[0]:
            return ""
        
        def clean(cell_text):
            if cell_text is None:
                return ""
            return re.sub(r'\s+', ' ', str(cell_text).strip())

        cleaned_table = [[clean(cell) for cell in row] for row in table]
        
        header = "| " + " | ".join(cleaned_table[0]) + " |"
        separator = "| " + " | ".join(["---"] * len(cleaned_table[0])) + " |"
        body = "\n".join(["| " + " | ".join(row) + " |" for row in cleaned_table[1:]])
        
        return f"{header}\n{separator}\n{body}"
