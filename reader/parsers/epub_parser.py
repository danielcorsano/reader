"""EPUB file parser implementation."""
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Any
import warnings
import sys

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
            # Suppress the specific FutureWarning from ebooklib's xpath usage
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", 
                                      message=".*This search incorrectly ignores the root element.*",
                                      category=FutureWarning)
                book = epub.read_epub(str(file_path))
            
            # Quick text length analysis before processing
            print(f"📖 Analyzing EPUB: {file_path.name}", file=sys.stderr)
            estimated_size = self._estimate_text_size(book)
            print(f"📊 Estimated text length: ~{estimated_size:,} characters", file=sys.stderr)
            
            if estimated_size > 500000:  # ~500K characters
                print(f"⚠️  Large book detected. Processing may take several minutes...", file=sys.stderr)
            
            # Extract metadata
            title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else file_path.stem
            author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown"
            
            metadata = {
                'title': title,
                'author': author,
                'language': book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else 'en',
                'format': 'EPUB'
            }
            
            # Extract text content with optimized processing
            chapters = []
            full_text = []
            processed_items = 0
            
            # Get all document items first to show progress
            document_items = [item for item in book.get_items() 
                            if item.get_type() == ebooklib.ITEM_DOCUMENT]
            total_items = len(document_items)
            
            print(f"📚 Processing {total_items} chapters...", file=sys.stderr)
            
            for i, item in enumerate(document_items, 1):
                # Show progress for large books
                if total_items > 10 and i % max(1, total_items // 10) == 0:
                    print(f"📖 Progress: {i}/{total_items} chapters ({i/total_items*100:.0f}%)", file=sys.stderr)
                
                # Optimize BeautifulSoup parsing for large documents
                content = item.get_content()
                if len(content) > 100000:  # Large chapter
                    # Use faster parser for large content
                    soup = BeautifulSoup(content, 'lxml' if self._has_lxml() else 'html.parser')
                else:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Extract text more efficiently
                text = self._extract_text_optimized(soup)
                
                if text.strip():
                    chapter_info = {
                        'title': item.get_name(),
                        'content': text,
                        'start_pos': len(' '.join(full_text))
                    }
                    chapters.append(chapter_info)
                    full_text.append(text)
                    processed_items += 1
            
            print(f"✅ Processed {processed_items} chapters successfully", file=sys.stderr)
            content = ' '.join(full_text)
            
            return ParsedContent(
                title=title,
                content=content,
                chapters=chapters,
                metadata=metadata
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse EPUB file {file_path}: {str(e)}")
    
    def _estimate_text_size(self, book) -> int:
        """Estimate the total text size in the EPUB without full parsing."""
        total_size = 0
        item_count = 0
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Quick estimation: HTML content length as proxy for text length
                content_length = len(item.get_content())
                # Estimate text is roughly 30-40% of HTML content length
                estimated_text = int(content_length * 0.35)
                total_size += estimated_text
                item_count += 1
                
                # Early exit for very large books to avoid long analysis
                if item_count >= 50 and total_size > 1000000:
                    return total_size
        
        return total_size
    
    def _has_lxml(self) -> bool:
        """Check if lxml parser is available."""
        try:
            import lxml
            return True
        except ImportError:
            return False
    
    def _extract_text_optimized(self, soup) -> str:
        """Extract text from BeautifulSoup with optimizations."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text with optimized settings
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()