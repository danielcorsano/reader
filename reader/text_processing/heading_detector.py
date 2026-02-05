"""Tiered chapter detection from extracted text.

Three-tier fallback:
1. Marked chapters — parser already provided real titles (not "Page N")
2. Headings — known section names, short isolated title-like lines
3. Formatting — ALL CAPS lines, indentation/spacing patterns
"""
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


class HeadingDetector:
    """Tiered chapter detection for any text source."""

    # Tier 2: known section heading patterns (case-insensitive)
    KNOWN_SECTIONS = {
        # Front matter
        r"Translator'?s?\s+Note", r"Editor'?s?\s+Note", r"Author'?s?\s+Note",
        r"Preface", r"Foreword", r"Introduction", r"Prologue",
        r"A\s+Note\s+on\s+the\s+Text", r"Acknowledgm?ents?",
        r"Dedication",
        # Structural
        r"Part\s+[IVXLCDMivxlcdm\d]+(?:\s*[:\-—]\s*.+)?",
        r"Book\s+[IVXLCDMivxlcdm\d]+(?:\s*[:\-—]\s*.+)?",
        r"Chapter\s+[IVXLCDMivxlcdm\d]+(?:\s*[:\-—]\s*.+)?",
        r"Section\s+[IVXLCDMivxlcdm\d]+(?:\s*[:\-—]\s*.+)?",
        r"Act\s+[IVXLCDMivxlcdm\d]+", r"Scene\s+[IVXLCDMivxlcdm\d]+",
        # Back matter
        r"Epilogue", r"Afterword", r"Postscript",
        r"Appendix(?:\s+[A-Za-z\d]+)?", r"Appendices",
        r"Index", r"Glossary", r"Bibliography", r"References",
        r"Notes?", r"Endnotes?", r"Footnotes?",
        r"Further\s+Reading", r"Suggested\s+Reading",
        r"Chronology", r"Timeline",
        r"About\s+the\s+Author",
        r"Table\s+of\s+Contents", r"Contents",
    }

    # Lines that are never headings
    _RE_NUMBERED_PARA = re.compile(r'^\d+\.\s+[a-z""\u201c]')
    _RE_BARE_NUMBER = re.compile(r'^\d+$')
    _RE_PAGE_HEADER = re.compile(r'^\d+\s+[A-Z]|[A-Z]\s+\d+$')
    _RE_MID_SENTENCE = re.compile(r'^[a-z]')  # starts lowercase = continuation

    def __init__(self):
        self._known_re = re.compile(
            r'^(?:' + '|'.join(self.KNOWN_SECTIONS) + r')\.?\s*$',
            re.IGNORECASE
        )

    def detect(self, text: str, chapters: Optional[List[Dict]] = None) -> List[Dict]:
        """Tiered chapter detection.

        Args:
            text: full extracted text
            chapters: parser-provided chapters (may be page-based)

        Returns list of {'title': str, 'content': str} dicts, or empty list
        if no structure detected.
        """
        # Tier 1: already marked chapters
        if chapters and not self._is_page_based(chapters):
            return chapters

        text = self._deduplicate_facing_pages(text)
        lines = text.split('\n')

        # Tier 2: heading detection (known names, isolated title-like lines)
        headings = self._find_headings(lines)
        if headings and len(headings) >= 2:
            return self._split_at_headings(lines, headings)

        # Tier 3: formatting-based (ALL CAPS, indentation patterns)
        format_headings = self._find_by_formatting(lines)
        if format_headings and len(format_headings) >= 2:
            return self._split_at_headings(lines, format_headings)

        return []

    def _is_page_based(self, chapters: List[Dict]) -> bool:
        """Check if chapters are just page-numbered (no real titles)."""
        page_re = re.compile(r'^Page\s+\d+$', re.IGNORECASE)
        return all(page_re.match(ch.get('title', '')) for ch in chapters)

    # --- Tier 2: Heading detection ---

    def _find_headings(self, lines: List[str]) -> List[Tuple[int, str]]:
        """Find heading lines by known names and isolated short title lines."""
        headings = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or len(stripped) < 2 or len(stripped) > 80:
                continue
            if self._is_noise(stripped):
                continue

            # Known section patterns (case-insensitive)
            if self._known_re.match(stripped):
                headings.append((i, stripped))
                continue

            # Short isolated line that looks like a title:
            # - under 60 chars, doesn't start lowercase
            # - blank line BOTH before AND after (fully isolated)
            # - doesn't end with sentence punctuation (not a sentence)
            # - doesn't contain commas (not a list item)
            if len(stripped) <= 60 and not self._RE_MID_SENTENCE.match(stripped):
                has_blank_before = (i == 0 or not lines[i - 1].strip())
                has_blank_after = (i == len(lines) - 1 or not lines[i + 1].strip())
                if has_blank_before and has_blank_after:
                    if not stripped[-1] in '.!?,;:' and ',' not in stripped:
                        if any(c.isalpha() for c in stripped):
                            headings.append((i, stripped))

        return headings

    # --- Tier 3: Formatting-based detection ---

    def _find_by_formatting(self, lines: List[str]) -> List[Tuple[int, str]]:
        """Detect chapters by formatting: ALL CAPS, indentation shifts."""
        headings = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or len(stripped) < 3 or len(stripped) > 60:
                continue
            if self._is_noise(stripped):
                continue

            # ALL CAPS lines with blank-line context
            alpha_chars = [c for c in stripped if c.isalpha()]
            if len(alpha_chars) >= 3 and all(c.isupper() for c in alpha_chars):
                if self._RE_PAGE_HEADER.match(stripped):
                    continue
                has_blank_before = (i == 0 or not lines[i - 1].strip())
                has_blank_after = (i == len(lines) - 1 or not lines[i + 1].strip())
                if has_blank_before or has_blank_after:
                    headings.append((i, stripped))

        return headings

    # --- Shared helpers ---

    def _is_noise(self, stripped: str) -> bool:
        """Filter lines that are never headings."""
        if self._RE_BARE_NUMBER.match(stripped):
            return True
        if self._RE_NUMBERED_PARA.match(stripped):
            return True
        return False

    def _deduplicate_facing_pages(self, text: str) -> str:
        """Remove near-duplicate consecutive blocks (bilingual facing pages)."""
        lines = text.split('\n')
        block_size = 50

        if len(lines) < block_size * 2:
            return text

        blocks = []
        for i in range(0, len(lines), block_size):
            blocks.append(lines[i:i + block_size])

        kept = [blocks[0]]
        for i in range(1, len(blocks)):
            prev_text = ' '.join(kept[-1]).strip()
            curr_text = ' '.join(blocks[i]).strip()
            if not prev_text or not curr_text:
                kept.append(blocks[i])
                continue
            ratio = SequenceMatcher(None, prev_text[:500], curr_text[:500]).ratio()
            if ratio < 0.80:
                kept.append(blocks[i])

        result_lines = []
        for block in kept:
            result_lines.extend(block)
        return '\n'.join(result_lines)

    def _split_at_headings(self, lines: List[str],
                           headings: List[Tuple[int, str]]) -> List[Dict]:
        """Split lines into chapters at heading positions."""
        chapters = []

        # Content before first heading
        if headings[0][0] > 0:
            pre_content = '\n'.join(lines[:headings[0][0]]).strip()
            if pre_content and len(pre_content) > 50:
                chapters.append({'title': '(Untitled)', 'content': pre_content})

        for idx, (line_idx, title) in enumerate(headings):
            if idx + 1 < len(headings):
                end_idx = headings[idx + 1][0]
            else:
                end_idx = len(lines)
            content = '\n'.join(lines[line_idx + 1:end_idx]).strip()
            chapters.append({'title': title, 'content': content})

        return chapters
