"""PDF file parser implementation."""
import re
import PyPDF2
from pathlib import Path
from typing import List, Dict, Any

from ..interfaces.text_parser import TextParser, ParsedContent


class PDFParser(TextParser):
    """Parser for PDF format documents."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf'

    def get_supported_extensions(self) -> List[str]:
        return ['.pdf']

    @staticmethod
    def _clean_pdf_text(text: str) -> str:
        """Normalize text extracted by PyPDF2: fix tabs and whitespace.

        Preserves single newlines for downstream heading detection.
        Line break cleanup happens in _clean_paragraph_breaks (strip writer)
        and _chunk_text_intelligently (synthesis).
        """
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        # Collapse multiple spaces (but not newlines)
        text = re.sub(r'[^\S\n]+', ' ', text)
        # Rejoin hyphenated line breaks (e.g. "exam-\nple" -> "example")
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
        return text.strip()

    def parse(self, file_path: Path) -> ParsedContent:
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                metadata_obj = pdf_reader.metadata
                title = metadata_obj.get('/Title', file_path.stem) if metadata_obj else file_path.stem
                author = metadata_obj.get('/Author', 'Unknown') if metadata_obj else 'Unknown'

                metadata = {
                    'title': title,
                    'author': author,
                    'pages': len(pdf_reader.pages),
                    'format': 'PDF'
                }

                chapters = []
                full_text = []

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            text = self._clean_pdf_text(text)
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