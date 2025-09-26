"""PDF file parser implementation."""
import PyPDF2
from pathlib import Path
from typing import List, Dict, Any

from ..interfaces.text_parser import TextParser, ParsedContent


class PDFParser(TextParser):
    """Parser for PDF format documents."""
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if file is a PDF."""
        return file_path.suffix.lower() == '.pdf'
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.pdf']
    
    def parse(self, file_path: Path) -> ParsedContent:
        """Parse PDF file and extract text content."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract metadata
                metadata_obj = pdf_reader.metadata
                title = metadata_obj.get('/Title', file_path.stem) if metadata_obj else file_path.stem
                author = metadata_obj.get('/Author', 'Unknown') if metadata_obj else 'Unknown'
                
                metadata = {
                    'title': title,
                    'author': author,
                    'pages': len(pdf_reader.pages),
                    'format': 'PDF'
                }
                
                # Extract text content
                chapters = []
                full_text = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            chapter_info = {
                                'title': f'Page {page_num + 1}',
                                'content': text,
                                'start_pos': len(' '.join(full_text))
                            }
                            chapters.append(chapter_info)
                            full_text.append(text)
                    except Exception as e:
                        print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
                        continue
                
                content = ' '.join(full_text)
                
                return ParsedContent(
                    title=title,
                    content=content,
                    chapters=chapters,
                    metadata=metadata
                )
                
        except Exception as e:
            raise ValueError(f"Failed to parse PDF file {file_path}: {str(e)}")