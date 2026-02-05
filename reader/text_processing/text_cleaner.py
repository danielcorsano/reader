"""Text cleanup for improved TTS pronunciation and content filtering."""
import re
from typing import Set

from .content_classifier import ContentClassifier


class TextCleaner:
    """Clean text to fix pronunciation issues and remove non-narrative content."""

    # Chapters to skip (exact title match, case-insensitive) - legacy fallback
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
        self._classifier = ContentClassifier()

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

    def should_skip_chapter(self, title: str, content: str = "",
                            epub_type: str = "", guide_type: str = "") -> bool:
        """Determine if chapter should be skipped.

        Uses multi-signal classifier when content is provided,
        falls back to title-only matching otherwise.
        """
        result = self._classifier.classify(
            title=title, content=content,
            epub_type=epub_type, guide_type=guide_type,
        )
        return result.is_junk

    def extract_narrative_content(self, chapters: list) -> str:
        """Extract only narrative content by finding start/end boundaries.

        Uses multi-signal classifier to detect content boundaries.
        """
        if not chapters:
            return ""

        start_idx, end_idx = self._classifier.find_content_boundaries(chapters)

        narrative_chapters = chapters[start_idx:end_idx]
        return ' '.join(ch.get('content', '') for ch in narrative_chapters)
