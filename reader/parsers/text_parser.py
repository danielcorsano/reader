"""Plain text file parser implementation."""
from pathlib import Path
from typing import List, Dict, Any
import re

from ..interfaces.text_parser import TextParser, ParsedContent


class PlainTextParser(TextParser):
    """Parser for plain text files."""
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if file is a supported text format."""
        return file_path.suffix.lower() in self.get_supported_extensions()
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return ['.txt', '.md', '.rst']
    
    def parse(self, file_path: Path) -> ParsedContent:
        """Parse text file and extract content."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError("Could not decode file with any supported encoding")
            
            # Extract basic metadata
            title = file_path.stem
            
            metadata = {
                'title': title,
                'author': 'Unknown',
                'format': file_path.suffix.upper().lstrip('.'),
                'size_chars': len(content)
            }
            
            # Simple chapter detection for markdown files
            chapters = []
            if file_path.suffix.lower() == '.md':
                chapters = self._detect_markdown_chapters(content)
            else:
                chapters = self._detect_simple_chapters(content)
            
            return ParsedContent(
                title=title,
                content=content,
                chapters=chapters,
                metadata=metadata
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse text file {file_path}: {str(e)}")
    
    def _detect_markdown_chapters(self, content: str) -> List[Dict[str, Any]]:
        """Detect chapters in markdown content based on headers."""
        chapters = []
        lines = content.split('\n')
        current_chapter = []
        chapter_title = "Introduction"
        start_pos = 0
        
        for line in lines:
            # Check for markdown headers
            if re.match(r'^#{1,3}\s+', line):
                # Save previous chapter if it has content
                if current_chapter:
                    chapter_content = '\n'.join(current_chapter)
                    chapters.append({
                        'title': chapter_title,
                        'content': chapter_content,
                        'start_pos': start_pos
                    })
                    start_pos += len(chapter_content) + 1
                
                # Start new chapter
                chapter_title = re.sub(r'^#{1,3}\s+', '', line).strip()
                current_chapter = []
            else:
                current_chapter.append(line)
        
        # Add final chapter
        if current_chapter:
            chapter_content = '\n'.join(current_chapter)
            chapters.append({
                'title': chapter_title,
                'content': chapter_content,
                'start_pos': start_pos
            })
        
        return chapters
    
    def _detect_simple_chapters(self, content: str) -> List[Dict[str, Any]]:
        """Simple chapter detection for plain text."""
        # Split by common chapter indicators
        chapter_patterns = [
            r'\n\s*Chapter\s+\d+',
            r'\n\s*CHAPTER\s+\d+',
            r'\n\s*\d+\.\s*[A-Z]',
        ]
        
        chapters = []
        remaining_content = content
        start_pos = 0
        chapter_num = 1
        
        for pattern in chapter_patterns:
            splits = re.split(pattern, remaining_content)
            if len(splits) > 1:
                # Found chapter breaks
                for i, section in enumerate(splits):
                    if section.strip():
                        chapters.append({
                            'title': f'Chapter {chapter_num}' if i > 0 else 'Introduction',
                            'content': section.strip(),
                            'start_pos': start_pos
                        })
                        start_pos += len(section) + 1
                        if i > 0:
                            chapter_num += 1
                return chapters
        
        # No chapters detected, treat as single chapter
        return [{
            'title': 'Complete Text',
            'content': content,
            'start_pos': 0
        }]