"""Text cleanup for improved TTS pronunciation and content filtering."""
import re
from typing import Set


class TextCleaner:
    """Clean text to fix pronunciation issues and remove non-narrative content."""

    # Chapters to skip (exact title match, case-insensitive)
    SKIP_CHAPTERS: Set[str] = {
        'bibliography', 'references', 'index',
        'also by', 'about the author', 'acknowledgments',
        'other works', 'praise for', 'notes',
        'contents', 'table of contents',
        'about the publisher', 'novels and story collections',
        'books by'
    }

    def __init__(self):
        # Pre-compile patterns for performance
        self.hyphen_break = re.compile(r'(\w+)-\s*\n\s*(\w+)')
        self.isbn_line = re.compile(r'^.*ISBN[-:\s]*\d{10,13}.*$', re.MULTILINE | re.IGNORECASE)
        # Detect book catalogs: 5+ capitalized titles without proper punctuation
        self.catalog_pattern = re.compile(r'([A-Z][A-Za-z\s]{10,60}\s*){5,}', re.MULTILINE)

    def clean(self, text: str, fix_words: bool = True, remove_metadata: bool = True) -> str:
        """
        Clean text for better TTS processing.

        Args:
            text: Input text to clean
            fix_words: Fix broken words (hyphenation, line breaks)
            remove_metadata: Remove ISBN and metadata lines

        Returns:
            Cleaned text
        """
        if fix_words:
            text = self._fix_broken_words(text)

        if remove_metadata:
            text = self._remove_metadata_lines(text)

        return text

    def _fix_broken_words(self, text: str) -> str:
        """Fix words broken by hyphens and line breaks."""
        # Fix hyphenated words split across lines: "exam-\nple" → "example"
        text = self.hyphen_break.sub(r'\1\2', text)
        return text

    def _remove_metadata_lines(self, text: str) -> str:
        """Remove standalone ISBN and metadata lines."""
        # Remove ISBN lines
        text = self.isbn_line.sub('', text)

        # Remove book catalog sections (e.g., "LE GUIN NOVELS Always Coming Home The Beginning Place...")
        # Only remove if it's a large block of capitalized titles
        for match in self.catalog_pattern.finditer(text):
            catalog_text = match.group(0)
            # Only remove if it's long enough to be a real catalog (> 200 chars)
            if len(catalog_text) > 200:
                text = text.replace(catalog_text, '')

        return text

    def should_skip_chapter(self, title: str) -> bool:
        """
        Determine if chapter should be skipped based on title.

        Args:
            title: Chapter title

        Returns:
            True if chapter should be skipped
        """
        title_lower = title.lower().strip()

        # Exact match or contains skip keyword
        for skip_term in self.SKIP_CHAPTERS:
            if skip_term == title_lower or title_lower.startswith(skip_term):
                return True

        return False

    def extract_narrative_content(self, chapters: list) -> str:
        """
        Extract only narrative content by finding start/end boundaries.

        Args:
            chapters: List of chapter dicts with 'title' and 'content'

        Returns:
            Combined narrative content only
        """
        if not chapters:
            return ""

        # Find first narrative chapter (skip front matter)
        start_idx = 0
        for i, ch in enumerate(chapters):
            if not self.should_skip_chapter(ch.get('title', '')):
                start_idx = i
                break

        # Find last narrative chapter (skip back matter)
        end_idx = len(chapters)
        for i in range(len(chapters) - 1, -1, -1):
            if not self.should_skip_chapter(chapters[i].get('title', '')):
                end_idx = i + 1
                break

        # Extract only narrative chapters
        narrative_chapters = chapters[start_idx:end_idx]
        return ' '.join(ch.get('content', '') for ch in narrative_chapters)
