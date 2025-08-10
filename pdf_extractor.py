import pdfplumber
import pathlib
import os
from typing import List, Dict, Any
import re

class PDFTableExtractor:
    """
    A modular class to extract tables from PDF files using pdfplumber
    and convert them to markdown format
    """
    
    def __init__(self, downloads_dir: str = "downloads"):
        """
        Initialize the PDF extractor
        
        Args:
            downloads_dir (str): Directory containing PDF files
        """
        self.downloads_dir = pathlib.Path(downloads_dir)
        self.output_dir = pathlib.Path("extracted_tables")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
    
    def get_pdf_files(self) -> List[pathlib.Path]:
        """
        Get all PDF files from the downloads directory
        
        Returns:
            List[pathlib.Path]: List of PDF file paths
        """
        if not self.downloads_dir.exists():
            print(f"❌ Downloads directory '{self.downloads_dir}' not found")
            return []
        
        pdf_files = list(self.downloads_dir.glob("*.pdf"))
        print(f"📁 Found {len(pdf_files)} PDF files in {self.downloads_dir}")
        return pdf_files
    
    def extract_tables_from_pdf(self, pdf_path: pathlib.Path) -> Dict[str, Any]:
        """
        Extract all tables from a single PDF file
        
        Args:
            pdf_path (pathlib.Path): Path to the PDF file
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted data
        """
        print(f"📄 Processing: {pdf_path.name}")
        
        extracted_data = {
            'filename': pdf_path.name,
            'tables': [],
            'text_content': [],
            'metadata': {}
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                extracted_data['metadata'] = {
                    'pages': len(pdf.pages),
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                    'subject': pdf.metadata.get('Subject', ''),
                    'creator': pdf.metadata.get('Creator', '')
                }
                
                print(f"   📊 PDF has {len(pdf.pages)} pages")
                
                # Process each page
                for page_num, page in enumerate(pdf.pages):
                    print(f"   📄 Processing page {page_num + 1}")
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        print(f"      🗂️  Found {len(tables)} tables on page {page_num + 1}")
                        
                        for table_num, table in enumerate(tables):
                            if table and any(any(cell for cell in row if cell) for row in table):
                                table_data = {
                                    'page': page_num + 1,
                                    'table_number': table_num + 1,
                                    'data': table,
                                    'markdown': self._table_to_markdown(table)
                                }
                                extracted_data['tables'].append(table_data)
                    
                    # Extract text content
                    text = page.extract_text()
                    if text and text.strip():
                        extracted_data['text_content'].append({
                            'page': page_num + 1,
                            'text': text.strip()
                        })
                
                print(f"   ✅ Extracted {len(extracted_data['tables'])} tables and {len(extracted_data['text_content'])} text sections")
                
        except Exception as e:
            print(f"   ❌ Error processing {pdf_path.name}: {e}")
            extracted_data['error'] = str(e)
        
        return extracted_data
    
    def extract_tables_from_pdf_bytes(self, pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all tables from PDF bytes in memory
        
        Args:
            pdf_data (Dict[str, Any]): PDF data dictionary with 'pdf_bytes' key
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted data
        """
        import io
        
        print(f"📄 Processing: {pdf_data['filename']}")
        
        extracted_data = {
            'filename': pdf_data['filename'],
            'tables': [],
            'text_content': [],
            'metadata': {}
        }
        
        try:
            # Create file-like object from bytes
            pdf_stream = io.BytesIO(pdf_data['pdf_bytes'])
            
            with pdfplumber.open(pdf_stream) as pdf:
                # Extract metadata
                extracted_data['metadata'] = {
                    'pages': len(pdf.pages),
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                    'subject': pdf.metadata.get('Subject', ''),
                    'creator': pdf.metadata.get('Creator', ''),
                    'size_bytes': pdf_data['size_bytes']
                }
                
                print(f"   📊 PDF has {len(pdf.pages)} pages")
                
                # Process each page
                for page_num, page in enumerate(pdf.pages):
                    print(f"   📄 Processing page {page_num + 1}")
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        print(f"      🗂️  Found {len(tables)} tables on page {page_num + 1}")
                        
                        for table_num, table in enumerate(tables):
                            if table and any(any(cell for cell in row if cell) for row in table):
                                table_data = {
                                    'page': page_num + 1,
                                    'table_number': table_num + 1,
                                    'data': table,
                                    'markdown': self._table_to_markdown(table)
                                }
                                extracted_data['tables'].append(table_data)
                    
                    # Extract text content
                    text = page.extract_text()
                    if text and text.strip():
                        extracted_data['text_content'].append({
                            'page': page_num + 1,
                            'text': text.strip()
                        })
                
                print(f"   ✅ Extracted {len(extracted_data['tables'])} tables and {len(extracted_data['tables'])} text sections")
                
        except Exception as e:
            print(f"   ❌ Error processing PDF: {e}")
            extracted_data['error'] = str(e)
        
        return extracted_data
    
    def _table_to_markdown(self, table: List[List[str]]) -> str:
        """
        Convert a table to markdown format
        
        Args:
            table (List[List[str]]): Table data as 2D list
            
        Returns:
            str: Markdown formatted table
        """
        if not table or not table[0]:
            return ""
        
        # Clean and normalize table data
        cleaned_table = []
        for row in table:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cell = ""
                # Clean up whitespace and newlines
                cell = re.sub(r'\s+', ' ', str(cell).strip())
                cleaned_row.append(cell)
            cleaned_table.append(cleaned_row)
        
        # Find the maximum width for each column
        col_widths = []
        for col_idx in range(len(cleaned_table[0])):
            max_width = 0
            for row in cleaned_table:
                if col_idx < len(row):
                    max_width = max(max_width, len(row[col_idx]))
            col_widths.append(max_width)
        
        markdown_lines = []
        
        # Add table header
        header_row = cleaned_table[0]
        markdown_lines.append("| " + " | ".join(header_row) + " |")
        
        # Add separator row
        separator = "| " + " | ".join(["-" * max(3, width) for width in col_widths]) + " |"
        markdown_lines.append(separator)
        
        # Add data rows
        for row in cleaned_table[1:]:
            if any(cell for cell in row if cell):  # Skip empty rows
                markdown_lines.append("| " + " | ".join(row) + " |")
        
        return "\n".join(markdown_lines)
    
    def save_to_markdown(self, extracted_data: Dict[str, Any], output_filename: str = None) -> str:
        """
        Save extracted data to a markdown file
        
        Args:
            extracted_data (Dict[str, Any]): Extracted data from PDF
            output_filename (str, optional): Custom output filename
            
        Returns:
            str: Path to the saved markdown file
        """
        if output_filename is None:
            # Generate filename from PDF name
            pdf_name = pathlib.Path(extracted_data['filename']).stem
            output_filename = f"{pdf_name}_extracted.md"
        
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# Extracted Data from: {extracted_data['filename']}\n\n")
            
            # Write metadata
            if extracted_data['metadata']:
                f.write("## Document Metadata\n\n")
                for key, value in extracted_data['metadata'].items():
                    f.write(f"- **{key.title()}**: {value}\n")
                f.write("\n")
            
            # Write tables
            if extracted_data['tables']:
                f.write("## Extracted Tables\n\n")
                
                for i, table_info in enumerate(extracted_data['tables']):
                    f.write(f"### Table {table_info['table_number']} (Page {table_info['page']})\n\n")
                    f.write(table_info['markdown'])
                    f.write("\n\n")
            
            # Write text content
            if extracted_data['text_content']:
                f.write("## Extracted Text Content\n\n")
                
                for text_section in extracted_data['text_content']:
                    f.write(f"### Page {text_section['page']}\n\n")
                    f.write(f"```\n{text_section['text']}\n```\n\n")
            
            # Write error if any
            if 'error' in extracted_data:
                f.write("## Errors\n\n")
                f.write(f"❌ {extracted_data['error']}\n")
        
        print(f"💾 Saved markdown to: {output_path}")
        return str(output_path)
    
    def process_all_pdfs(self) -> List[str]:
        """
        Process all PDF files in the downloads directory
        
        Returns:
            List[str]: List of paths to generated markdown files
        """
        pdf_files = self.get_pdf_files()
        if not pdf_files:
            return []
        
        generated_files = []
        
        for pdf_file in pdf_files:
            print(f"\n{'='*60}")
            extracted_data = self.extract_tables_from_pdf(pdf_file)
            
            if extracted_data['tables'] or extracted_data['text_content']:
                markdown_file = self.save_to_markdown(extracted_data)
                generated_files.append(markdown_file)
            else:
                print(f"   ⚠️  No extractable content found in {pdf_file.name}")
        
        print(f"\n{'='*60}")
        print(f"🎉 Processing complete! Generated {len(generated_files)} markdown files")
        return generated_files
    
    def process_specific_pdf(self, pdf_filename: str) -> str:
        """
        Process a specific PDF file by name
        
        Args:
            pdf_filename (str): Name of the PDF file to process
            
        Returns:
            str: Path to the generated markdown file
        """
        pdf_path = self.downloads_dir / pdf_filename
        
        if not pdf_path.exists():
            print(f"❌ PDF file '{pdf_filename}' not found in {self.downloads_dir}")
            return ""
        
        print(f"\n{'='*60}")
        extracted_data = self.extract_tables_from_pdf(pdf_path)
        
        if extracted_data['tables'] or extracted_data['text_content']:
            markdown_file = self.save_to_markdown(extracted_data)
            return markdown_file
        else:
            print(f"   ⚠️  No extractable content found in {pdf_filename}")
            return ""


def main():
    """
    Main function to demonstrate usage
    """
    print("🚀 PDF Table Extractor")
    print("=" * 50)
    
    # Initialize extractor
    extractor = PDFTableExtractor()
    
    # Process all PDFs
    generated_files = extractor.process_all_pdfs()
    
    if generated_files:
        print(f"\n📁 Generated files:")
        for file_path in generated_files:
            print(f"   📄 {file_path}")
    else:
        print("\n❌ No files were generated")


if __name__ == "__main__":
    main()
