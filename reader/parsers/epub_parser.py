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
                warnings.filterwarnings("ignore", 
                                      message=".*ignore_ncx.*",
                                      category=UserWarning)
                book = epub.read_epub(str(file_path), options={'ignore_ncx': True})
            
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
            
            # Extract text content using spine order with content filtering
            chapters = []
            full_text = []
            processed_items = 0
            
            # Get spine items (proper reading order) and filter content
            spine_items = self._get_filtered_spine_items(book)
            total_items = len(spine_items)
            
            print(f"📚 Processing {total_items} content sections in reading order...", file=sys.stderr)
            
            for i, item in enumerate(spine_items, 1):
                # Show progress for large books
                if total_items > 10 and i % max(1, total_items // 10) == 0:
                    print(f"📖 Progress: {i}/{total_items} sections ({i/total_items*100:.0f}%)", file=sys.stderr)
                
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
                        'title': self._extract_title_from_html(soup) or item.get_name(),
                        'content': text,
                        'start_pos': len(' '.join(full_text))
                    }
                    chapters.append(chapter_info)
                    full_text.append(text)
                    processed_items += 1
            
            print(f"✅ Processed {processed_items} content sections successfully", file=sys.stderr)
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
    
    def _get_filtered_spine_items(self, book):
        """Get spine items in reading order, filtered to exclude unwanted content."""
        spine_items = []
        
        for item_id, linear in book.spine:
            item = book.get_item_with_id(item_id)
            if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Filter out unwanted content
                if self._should_include_item(item):
                    spine_items.append(item)
        
        return spine_items
    
    def _should_include_item(self, item) -> bool:
        """Determine if an EPUB item should be included in the audiobook."""
        item_name = item.get_name().lower()
        
        # Exclude cover pages
        if any(x in item_name for x in ['cover', 'title.html']):
            return False
        
        # Exclude table of contents
        if any(x in item_name for x in ['toc.html', 'contents']):
            return False
            
        # Exclude back matter (index, notes, copyright, etc.)
        if any(x in item_name for x in ['index.html', 'notes.html', 'copy.html', 'dsi.html', 'copyright']):
            return False
        
        # Exclude image-only sections
        if '_img.html' in item_name:
            return False
        
        # Check content length - exclude very short sections (likely navigation)
        try:
            content = item.get_content()
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text(strip=True)
            
            # Exclude if too short (likely just navigation or formatting)
            if len(text) < 100:
                return False
                
        except Exception:
            # If we can't parse it, exclude it
            return False
        
        # Include forewords, introductions, and chapters
        if any(x in item_name for x in ['fw.html', 'intro', 'foreword', 'preface']):
            return True
            
        # Include main chapters (c1.html, c2.html, etc.)
        if any(x in item_name for x in ['c1.html', 'c2.html', 'c3.html', 'c4.html', 'c5.html', 'c6.html', 'c7.html', 'c8.html', 'c9.html']) or '/c' in item_name:
            return True
            
        # Default: include if it passes the length check above
        return True
    
    def _extract_title_from_html(self, soup):
        """Extract chapter title from HTML soup."""
        # Look for common title tags
        title_tags = ['h1', 'h2', 'h3', 'title']
        
        for tag in title_tags:
            element = soup.find(tag)
            if element and element.get_text(strip=True):
                title = element.get_text(strip=True)
                # Clean up title and check reasonable length
                if len(title) < 200:  # Reasonable title length
                    return title
        
        return None