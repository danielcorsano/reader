"""Chapter management and metadata extraction for Phase 3."""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import json


@dataclass
class ChapterInfo:
    """Information about a book chapter."""
    title: str
    start_time: float = 0.0  # Start time in seconds
    end_time: Optional[float] = None  # End time in seconds
    duration: Optional[float] = None  # Duration in seconds
    word_count: int = 0
    text_content: str = ""
    chapter_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChapterInfo':
        """Create from dictionary."""
        return cls(**data)


class ChapterManager:
    """Manages chapter detection, extraction, and metadata."""
    
    # Common chapter patterns for different sources
    CHAPTER_PATTERNS = [
        # Standard chapter headings
        r'^(Chapter\s+\d+.*?)$',
        r'^(CHAPTER\s+\d+.*?)$',
        r'^(\d+\.\s+.*?)$',
        r'^(Ch\.\s*\d+.*?)$',

        # Roman numerals - uppercase with "Chapter"
        r'^(Chapter\s+[IVXLCDM]+.*?)$',
        # Roman numerals - lowercase with "Chapter"
        r'^(Chapter\s+[ivxlcdm]+.*?)$',
        # Roman numerals - uppercase with period (IV. Title)
        r'^([IVXLCDM]+\.\s+.*?)$',
        # Roman numerals - lowercase with period (iv. Title)
        r'^([ivxlcdm]+\.\s+.*?)$',
        # Roman numerals - uppercase with colon (IV: Title)
        r'^([IVXLCDM]+:\s+.*?)$',
        # Roman numerals - lowercase with colon (iv: Title)
        r'^([ivxlcdm]+:\s+.*?)$',
        # Roman numerals - standalone uppercase at line start (IV or IV Title)
        r'^([IVXLCDM]+)(?:\s+[A-Z].*)?$',
        # Roman numerals - standalone lowercase at line start (iv or iv Title)
        r'^([ivxlcdm]+)(?:\s+[A-Za-z].*)?$',

        # Written numbers
        r'^(Chapter\s+(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve).*?)$',

        # Part/Section markers
        r'^(Part\s+\d+.*?)$',
        r'^(Part\s+[IVXLCDM]+.*?)$',
        r'^(Part\s+[ivxlcdm]+.*?)$',
        r'^(Section\s+\d+.*?)$',
        r'^(Book\s+\d+.*?)$',
        r'^(Book\s+[IVXLCDM]+.*?)$',

        # Special formats
        r'^(\*\s*\*\s*\*.*?)$',  # *** Chapter markers
        r'^(═+.*?)$',  # Decorative lines
        r'^(─+.*?)$',
    ]
    
    def __init__(self):
        """Initialize the chapter manager."""
        self.compiled_patterns = [re.compile(pattern, re.MULTILINE | re.IGNORECASE) 
                                for pattern in self.CHAPTER_PATTERNS]
    
    def extract_chapters_from_text(self, text: str, source_type: str = "text") -> List[ChapterInfo]:
        """
        Extract chapters from plain text.
        
        Args:
            text: The full text content
            source_type: Type of source ("text", "epub", "pdf")
            
        Returns:
            List of ChapterInfo objects
        """
        chapters = []
        
        # Try pattern-based detection first
        pattern_chapters = self._detect_chapters_by_pattern(text)
        
        if pattern_chapters:
            chapters.extend(pattern_chapters)
        else:
            # Fallback: split by paragraph breaks or page breaks
            fallback_chapters = self._detect_chapters_by_structure(text)
            chapters.extend(fallback_chapters)
        
        # Calculate word counts and clean up
        for i, chapter in enumerate(chapters):
            chapter.chapter_number = i + 1
            chapter.word_count = len(chapter.text_content.split())
            
            # Estimate duration based on average reading speed
            # Average audiobook speed: ~150-160 words per minute
            if chapter.word_count > 0:
                chapter.duration = chapter.word_count / 150.0 * 60.0  # Convert to seconds
        
        # Set start/end times
        current_time = 0.0
        for chapter in chapters:
            chapter.start_time = current_time
            chapter.end_time = current_time + (chapter.duration or 0)
            current_time = chapter.end_time
        
        return chapters
    
    def _detect_chapters_by_pattern(self, text: str) -> List[ChapterInfo]:
        """Detect chapters using regex patterns."""
        chapters = []
        chapter_positions = []
        
        # Find all chapter markers
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                chapter_title = match.group(1).strip()
                position = match.start()
                
                # Avoid duplicates at similar positions
                if not any(abs(pos - position) < 50 for pos, _ in chapter_positions):
                    chapter_positions.append((position, chapter_title))
        
        # Sort by position
        chapter_positions.sort(key=lambda x: x[0])
        
        # Extract text content for each chapter
        for i, (position, title) in enumerate(chapter_positions):
            # Find the end position (start of next chapter or end of text)
            if i + 1 < len(chapter_positions):
                end_position = chapter_positions[i + 1][0]
            else:
                end_position = len(text)
            
            # Extract chapter content
            chapter_text = text[position:end_position].strip()
            
            # Remove the chapter title from content to avoid duplication
            lines = chapter_text.split('\n')
            if lines and title.lower() in lines[0].lower():
                chapter_text = '\n'.join(lines[1:]).strip()
            
            if chapter_text:  # Only add if there's actual content
                chapter = ChapterInfo(
                    title=title,
                    text_content=chapter_text
                )
                chapters.append(chapter)
        
        return chapters
    
    def _detect_chapters_by_structure(self, text: str) -> List[ChapterInfo]:
        """Fallback chapter detection using text structure."""
        chapters = []
        
        # Split by double line breaks (paragraph breaks)
        sections = text.split('\n\n')
        
        # Group sections into chapters (rough estimation)
        words_per_chapter = 2000  # Target words per chapter
        current_chapter_text = ""
        current_word_count = 0
        chapter_number = 1
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            section_words = len(section.split())
            
            # If adding this section would exceed target, finalize current chapter
            if current_word_count > 0 and current_word_count + section_words > words_per_chapter:
                if current_chapter_text:
                    chapter = ChapterInfo(
                        title=f"Chapter {chapter_number}",
                        text_content=current_chapter_text.strip()
                    )
                    chapters.append(chapter)
                    chapter_number += 1
                
                # Start new chapter
                current_chapter_text = section
                current_word_count = section_words
            else:
                # Add to current chapter
                if current_chapter_text:
                    current_chapter_text += "\n\n" + section
                else:
                    current_chapter_text = section
                current_word_count += section_words
        
        # Add the last chapter
        if current_chapter_text:
            chapter = ChapterInfo(
                title=f"Chapter {chapter_number}",
                text_content=current_chapter_text.strip()
            )
            chapters.append(chapter)
        
        return chapters
    
    def extract_chapters_from_epub(self, epub_path: Path) -> List[ChapterInfo]:
        """
        Extract chapters from EPUB file using structure metadata.
        
        Args:
            epub_path: Path to EPUB file
            
        Returns:
            List of ChapterInfo objects
        """
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("ebooklib and beautifulsoup4 required for EPUB processing")
        
        chapters = []
        
        try:
            book = epub.read_epub(str(epub_path))
            
            # Get chapters from spine (reading order)
            chapter_number = 1
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # Parse HTML content
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # Extract text content
                    text_content = soup.get_text(separator='\n', strip=True)
                    
                    if text_content and len(text_content.strip()) > 100:  # Minimum content threshold
                        # Try to extract chapter title
                        title = self._extract_title_from_html(soup)
                        if not title:
                            title = f"Chapter {chapter_number}"
                        
                        chapter = ChapterInfo(
                            title=title,
                            text_content=text_content,
                            chapter_number=chapter_number
                        )
                        chapters.append(chapter)
                        chapter_number += 1
            
            # Calculate timing information
            self._calculate_chapter_timing(chapters)
            
            return chapters
            
        except Exception as e:
            print(f"Warning: Failed to extract EPUB chapters: {e}")
            # Fallback to text-based extraction
            return []
    
    def _extract_title_from_html(self, soup) -> Optional[str]:
        """Extract chapter title from HTML soup."""
        # Look for common title tags
        title_tags = ['h1', 'h2', 'h3', 'title']
        
        for tag in title_tags:
            element = soup.find(tag)
            if element and element.get_text(strip=True):
                title = element.get_text(strip=True)
                # Clean up title
                if len(title) < 200:  # Reasonable title length
                    return title
        
        return None
    
    def extract_chapters_from_pdf(self, pdf_path: Path) -> List[ChapterInfo]:
        """
        Extract chapters from PDF file using outline/bookmarks.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of ChapterInfo objects
        """
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 required for PDF processing")
        
        chapters = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Try to extract bookmarks/outline
                if pdf_reader.outline:
                    chapters = self._extract_pdf_bookmarks(pdf_reader)
                
                # If no bookmarks, fallback to text-based detection
                if not chapters:
                    # Extract all text first
                    full_text = ""
                    for page in pdf_reader.pages:
                        full_text += page.extract_text() + "\n"
                    
                    chapters = self.extract_chapters_from_text(full_text, "pdf")
            
            return chapters
            
        except Exception as e:
            print(f"Warning: Failed to extract PDF chapters: {e}")
            return []
    
    def _extract_pdf_bookmarks(self, pdf_reader) -> List[ChapterInfo]:
        """Extract chapters from PDF bookmarks."""
        chapters = []
        
        def process_bookmark(bookmark, level=0):
            if isinstance(bookmark, list):
                for item in bookmark:
                    process_bookmark(item, level)
            else:
                title = bookmark.title
                
                # Only use top-level bookmarks as chapters
                if level == 0 and title:
                    chapter = ChapterInfo(
                        title=title,
                        text_content="",  # Will be populated later if needed
                    )
                    chapters.append(chapter)
        
        process_bookmark(pdf_reader.outline)
        
        # Number the chapters
        for i, chapter in enumerate(chapters):
            chapter.chapter_number = i + 1
        
        return chapters
    
    def _calculate_chapter_timing(self, chapters: List[ChapterInfo]) -> None:
        """Calculate timing information for chapters."""
        current_time = 0.0
        
        for chapter in chapters:
            chapter.start_time = current_time
            
            # Estimate duration based on word count
            if chapter.word_count == 0:
                chapter.word_count = len(chapter.text_content.split())
            
            # Average audiobook speed: ~150 words per minute
            chapter.duration = chapter.word_count / 150.0 * 60.0  # Convert to seconds
            chapter.end_time = current_time + chapter.duration
            
            current_time = chapter.end_time
    
    def save_chapters_metadata(self, chapters: List[ChapterInfo], output_path: Path) -> None:
        """
        Save chapter metadata to JSON file.
        
        Args:
            chapters: List of chapters to save
            output_path: Path for output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        chapters_data = {
            'chapters': [chapter.to_dict() for chapter in chapters],
            'total_chapters': len(chapters),
            'total_duration': sum(ch.duration or 0 for ch in chapters),
            'total_words': sum(ch.word_count for ch in chapters)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapters_data, f, indent=2, ensure_ascii=False)
    
    def load_chapters_metadata(self, metadata_path: Path) -> List[ChapterInfo]:
        """
        Load chapter metadata from JSON file.
        
        Args:
            metadata_path: Path to JSON metadata file
            
        Returns:
            List of ChapterInfo objects
        """
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chapters = []
        for chapter_data in data.get('chapters', []):
            chapter = ChapterInfo.from_dict(chapter_data)
            chapters.append(chapter)
        
        return chapters
    
    def merge_chapters(self, chapters: List[ChapterInfo], max_duration: float = 1800.0) -> List[ChapterInfo]:
        """
        Merge short chapters together to create more reasonable chapter lengths.
        
        Args:
            chapters: Original chapters list
            max_duration: Maximum duration per merged chapter in seconds (default: 30 minutes)
            
        Returns:
            List of merged chapters
        """
        if not chapters:
            return []
        
        merged_chapters = []
        current_chapter = None
        current_duration = 0.0
        
        for chapter in chapters:
            chapter_duration = chapter.duration or 0
            
            if current_chapter is None:
                # Start new merged chapter
                current_chapter = ChapterInfo(
                    title=chapter.title,
                    text_content=chapter.text_content,
                    start_time=chapter.start_time
                )
                current_duration = chapter_duration
            elif current_duration + chapter_duration <= max_duration:
                # Merge with current chapter
                current_chapter.title += f" / {chapter.title}"
                current_chapter.text_content += "\n\n" + chapter.text_content
                current_duration += chapter_duration
            else:
                # Finalize current chapter and start new one
                current_chapter.duration = current_duration
                current_chapter.end_time = current_chapter.start_time + current_duration
                current_chapter.word_count = len(current_chapter.text_content.split())
                merged_chapters.append(current_chapter)
                
                # Start new chapter
                current_chapter = ChapterInfo(
                    title=chapter.title,
                    text_content=chapter.text_content,
                    start_time=current_chapter.end_time
                )
                current_duration = chapter_duration
        
        # Add the last chapter
        if current_chapter:
            current_chapter.duration = current_duration
            current_chapter.end_time = current_chapter.start_time + current_duration
            current_chapter.word_count = len(current_chapter.text_content.split())
            merged_chapters.append(current_chapter)
        
        # Renumber chapters
        for i, chapter in enumerate(merged_chapters):
            chapter.chapter_number = i + 1
        
        return merged_chapters
    
    def get_chapter_statistics(self, chapters: List[ChapterInfo]) -> Dict[str, Any]:
        """Get statistics about the chapters."""
        if not chapters:
            return {}
        
        durations = [ch.duration or 0 for ch in chapters]
        word_counts = [ch.word_count for ch in chapters]
        
        return {
            'total_chapters': len(chapters),
            'total_duration': sum(durations),
            'total_duration_formatted': self._format_duration(sum(durations)),
            'average_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'total_words': sum(word_counts),
            'average_words_per_chapter': sum(word_counts) / len(word_counts) if word_counts else 0,
            'estimated_reading_time_hours': sum(word_counts) / 150.0 / 60.0  # 150 WPM
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"