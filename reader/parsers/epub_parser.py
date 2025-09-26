"""EPUB file parser implementation."""
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Any

from ..interfaces.text_parser import TextParser, ParsedContent


class EPUBParser(TextParser):
    """Parser for EPUB format ebooks."""
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if file is an EPUB."""
        return file_path.suffix.lower() == '.epub'
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.epub']
    
    def parse(self, file_path: Path) -> ParsedContent:
        """Parse EPUB file and extract text content."""
        try:
            book = epub.read_epub(str(file_path))
            
            # Extract metadata
            title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else file_path.stem
            author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown"
            
            metadata = {
                'title': title,
                'author': author,
                'language': book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else 'en',
                'format': 'EPUB'
            }
            
            # Extract text content
            chapters = []
            full_text = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text(separator=' ', strip=True)
                    
                    if text.strip():
                        chapter_info = {
                            'title': item.get_name(),
                            'content': text,
                            'start_pos': len(' '.join(full_text))
                        }
                        chapters.append(chapter_info)
                        full_text.append(text)
            
            content = ' '.join(full_text)
            
            return ParsedContent(
                title=title,
                content=content,
                chapters=chapters,
                metadata=metadata
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse EPUB file {file_path}: {str(e)}")