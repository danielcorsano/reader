"""Multi-signal content classifier for detecting non-content chapters."""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ClassificationResult:
    """Result of classifying a chapter."""
    is_junk: bool
    junk_score: float  # 0.0 = content, 1.0 = junk
    signals: Dict[str, float] = field(default_factory=dict)
    category: str = ""  # e.g. "copyright", "toc", "index", "content"
    confidence: str = ""  # "high", "medium", "low"


class ContentClassifier:
    """Classify chapters as content or non-content using 4 weighted signals."""

    # --- Signal weights ---
    WEIGHT_TITLE = 0.35
    WEIGHT_EPUB = 0.40
    WEIGHT_PATTERNS = 0.30
    WEIGHT_DENSITY = 0.20

    # --- Classification thresholds ---
    BASE_JUNK_THRESHOLD = 0.7
    BASE_SUSPECT_THRESHOLD = 0.4
    SENSITIVITY_STEP = 0.1
    MULTI_SIGNAL_BOOST = 1.2

    # --- Content pattern thresholds ---
    COPYRIGHT_HIGH = 3
    COPYRIGHT_LOW = 1
    TOC_HIGH = 5
    TOC_LOW = 3
    INDEX_HIGH = 10
    INDEX_LOW = 5
    BIBLIOGRAPHY_HIGH = 5
    BIBLIOGRAPHY_LOW = 2
    PRAISE_HIGH = 3
    PRAISE_LOW = 1
    ABOUT_AUTHOR_THRESHOLD = 2

    # --- Prose density thresholds ---
    NUMERIC_DENSITY_HIGH = 0.20
    NUMERIC_DENSITY_LOW = 0.12
    AVG_LINE_LENGTH_SHORT = 30
    MIN_LINES_FOR_STRUCTURE = 10
    NUMBER_ENDING_RATIO = 0.4
    SENTENCE_DENSITY_LOW = 1.0
    COMMA_NUMBER_SEQUENCES = 5

    # --- Title keyword lists ---
    JUNK_TITLES_EXACT = {
        'bibliography', 'references', 'index', 'glossary',
        'contents', 'table of contents', 'endnotes', 'footnotes',
        'notes', 'copyright', 'copyright page', 'colophon',
        'about the author', 'about the authors', 'about the editor',
        'about the publisher', 'about the translator',
        'acknowledgments', 'acknowledgements',
        'also by', 'other books by', 'books by',
        'other works', 'other titles', 'novels and story collections',
        'praise for', 'praise', 'advance praise', 'reviews',
        'blurbs', 'endorsements', 'testimonials',
        'catalog', 'catalogue', 'backlist',
        'dedication', 'epigraph',
        'title page', 'half title', 'half-title',
        'frontispiece', 'list of illustrations', 'list of figures',
        'list of tables', 'list of maps', 'list of plates',
        'list of abbreviations', 'abbreviations',
        'permissions', 'credits', 'photo credits', 'image credits',
        'about this book', 'a note on the text',
        'further reading', 'suggested reading', 'recommended reading',
        'resources', 'appendix', 'appendices',
        'chronology', 'timeline',
        'dramatis personae', 'cast of characters',
    }

    JUNK_TITLES_PREFIX = {
        'also by', 'other books', 'books by', 'praise for',
        'copyright', 'about the', 'a note on', 'a note from',
        'list of', 'works by', 'novels by', 'selected',
        'further reading', 'suggested reading',
    }

    CONTENT_TITLES_EXACT = {
        'prologue', 'epilogue', 'introduction', 'foreword', 'preface',
        'afterword', 'postscript', 'interlude', 'intermezzo',
    }

    CONTENT_TITLES_PREFIX = {
        'chapter', 'part', 'book', 'act', 'scene', 'section',
        'prologue', 'epilogue', 'introduction', 'foreword', 'preface',
        'afterword',
    }

    # --- EPUB semantic types ---
    EPUB_JUNK_TYPES = {
        'copyright-page', 'colophon', 'toc', 'loi', 'lot', 'index',
        'glossary', 'bibliography', 'acknowledgments', 'dedication',
        'epigraph', 'titlepage', 'halftitlepage', 'imprint',
        'other-credits', 'errata', 'contributors',
    }

    EPUB_CONTENT_TYPES = {
        'bodymatter', 'chapter', 'prologue', 'epilogue', 'introduction',
        'foreword', 'preface', 'afterword', 'part', 'division',
        'volume', 'subchapter', 'preamble', 'conclusion',
    }

    # --- OPF guide reference types ---
    OPF_JUNK_TYPES = {
        'copyright-page', 'toc', 'loi', 'lot', 'index', 'glossary',
        'bibliography', 'colophon', 'title-page', 'dedication',
    }

    OPF_CONTENT_TYPES = {
        'text', 'bodymatter', 'preface', 'foreword', 'introduction',
    }

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns."""
        self._re_copyright = re.compile(
            r'(?:copyright|\u00a9|all rights reserved|ISBN[-:\s]*[\dX-]{10,}|'
            r'published by|first (?:edition|printing|published)|'
            r'printed in|library of congress|cataloging.in.publication|'
            r'no part of this (?:book|publication)|'
            r'permission .{0,40} publisher)',
            re.IGNORECASE
        )
        self._re_toc = re.compile(
            r'(?:^\s*(?:chapter|part|section)\s+[\divxlc]+\b.*\d+\s*$|'
            r'^\s*\d+\.\s+.{5,60}\s+\d+\s*$|'
            r'^\s*.{5,60}\.{3,}\s*\d+\s*$)',
            re.IGNORECASE | re.MULTILINE
        )
        self._re_index = re.compile(
            r'(?:^\s*[A-Z][a-z]+(?:,\s*\d[\d,\s-]*)+\s*$)',
            re.MULTILINE
        )
        self._re_bibliography = re.compile(
            r'(?:^\s*[A-Z][a-z]+,\s+[A-Z]\..*\(\d{4}\)|'
            r'^\s*\[\d+\]\s+|'
            r'(?:et al\.|pp?\.\s*\d+|vol\.\s*\d+|eds?\.|trans\.))',
            re.IGNORECASE | re.MULTILINE
        )
        self._re_praise = re.compile(
            r'(?:[\u201c\u201d"\'].{20,200}[\u201c\u201d"\']'
            r'\s*[-\u2014\u2013]\s*[A-Z][a-z]+ [A-Z]|'
            r'praise for\b|advance praise|'
            r'new york times|wall street journal|washington post|'
            r'bestselling author|award.winning)',
            re.IGNORECASE
        )
        self._re_about_author = re.compile(
            r'(?:is the author of|lives in|was born in|'
            r'has written|graduated from|teaches at|'
            r'is a (?:professor|writer|journalist|novelist|poet)|'
            r'her (?:novels?|books?|works?) include|'
            r'his (?:novels?|books?|works?) include)',
            re.IGNORECASE
        )
        self._re_catalog = re.compile(
            r'(?:^\s*[A-Z][A-Z\s]{5,50}\s*$(?:\s*[A-Z][A-Z\s]{5,50}\s*$){3,})',
            re.MULTILINE
        )
        self._re_comma_number = re.compile(r'\d+,\s*\d+')
        self._re_sentence_end = re.compile(r'[.!?]')
        self._re_digits = re.compile(r'\d')

    # --- Signal 1: Title classification ---

    def _score_title(self, title: str) -> Tuple[float, str]:
        """Score a chapter title. Returns (score, category)."""
        if not title:
            return 0.0, ""

        title_lower = title.lower().strip()

        # Content protection: never flag these
        for prefix in self.CONTENT_TITLES_PREFIX:
            if title_lower.startswith(prefix):
                return -1.0, "content"
        if title_lower in self.CONTENT_TITLES_EXACT:
            return -1.0, "content"

        # Exact match
        if title_lower in self.JUNK_TITLES_EXACT:
            return 1.0, self._categorize_title(title_lower)

        # Prefix match
        for prefix in self.JUNK_TITLES_PREFIX:
            if title_lower.startswith(prefix):
                return 1.0, self._categorize_title(prefix)

        # Numeric-only titles (e.g. bare roman numerals) are content
        if re.match(r'^[ivxlcdm\d\s.]+$', title_lower):
            return -1.0, "content"

        return 0.0, ""

    def _categorize_title(self, title_lower: str) -> str:
        """Map a title keyword to a category."""
        categories = {
            'copyright': ['copyright', 'permissions', 'credits'],
            'toc': ['contents', 'table of contents'],
            'index': ['index', 'glossary', 'abbreviations'],
            'bibliography': ['bibliography', 'references', 'notes', 'endnotes',
                           'footnotes', 'further reading', 'suggested reading',
                           'recommended reading'],
            'praise': ['praise', 'blurbs', 'endorsements', 'testimonials',
                      'reviews', 'advance praise'],
            'about_author': ['about the', 'a note on', 'a note from'],
            'catalog': ['also by', 'other books', 'books by', 'other works',
                       'other titles', 'novels', 'works by', 'selected',
                       'catalog', 'catalogue', 'backlist'],
            'front_matter': ['title page', 'half title', 'frontispiece',
                           'dedication', 'epigraph', 'list of'],
            'back_matter': ['appendix', 'appendices', 'chronology', 'timeline',
                          'resources', 'dramatis personae', 'cast of characters'],
        }
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in title_lower:
                    return cat
        return "junk"

    # --- Signal 2: EPUB semantic attributes ---

    def _score_epub_metadata(self, epub_type: str = "", guide_type: str = "") -> float:
        """Score based on EPUB semantic type and OPF guide type."""
        epub_lower = epub_type.lower().strip() if epub_type else ""
        guide_lower = guide_type.lower().strip() if guide_type else ""

        # Content types force score to 0
        if epub_lower in self.EPUB_CONTENT_TYPES or guide_lower in self.OPF_CONTENT_TYPES:
            return -1.0

        # Junk types
        if epub_lower in self.EPUB_JUNK_TYPES or guide_lower in self.OPF_JUNK_TYPES:
            return 1.0

        return 0.0

    # --- Signal 3: Content pattern detection ---

    def _score_patterns(self, text: str) -> Tuple[float, str]:
        """Score based on content patterns. Returns (score, category)."""
        if not text or len(text) < 50:
            return 0.0, ""

        # Sample first 3000 chars for pattern matching (performance)
        sample = text[:3000]

        # Copyright patterns
        hits = len(self._re_copyright.findall(sample))
        if hits >= self.COPYRIGHT_HIGH:
            return 1.0, "copyright"
        if hits >= self.COPYRIGHT_LOW:
            cp_score = 0.5 + 0.5 * (hits / self.COPYRIGHT_HIGH)
            # Check for short copyright pages (high density = high confidence)
            if len(text) < 1000 and hits >= 2:
                return 1.0, "copyright"
            return min(cp_score, 0.9), "copyright"

        # TOC patterns
        hits = len(self._re_toc.findall(text))
        if hits >= self.TOC_HIGH:
            return 1.0, "toc"
        if hits >= self.TOC_LOW:
            return 0.5 + 0.5 * (hits / self.TOC_HIGH), "toc"

        # Index patterns
        hits = len(self._re_index.findall(text[:5000]))
        if hits >= self.INDEX_HIGH:
            return 1.0, "index"
        if hits >= self.INDEX_LOW:
            return 0.5 + 0.5 * (hits / self.INDEX_HIGH), "index"

        # Bibliography patterns
        hits = len(self._re_bibliography.findall(text[:5000]))
        if hits >= self.BIBLIOGRAPHY_HIGH:
            return 1.0, "bibliography"
        if hits >= self.BIBLIOGRAPHY_LOW:
            return 0.5 + 0.5 * (hits / self.BIBLIOGRAPHY_HIGH), "bibliography"

        # Praise/blurbs
        hits = len(self._re_praise.findall(sample))
        if hits >= self.PRAISE_HIGH:
            return 1.0, "praise"
        if hits >= self.PRAISE_LOW:
            return 0.5 + 0.5 * (hits / self.PRAISE_HIGH), "praise"

        # About the author
        hits = len(self._re_about_author.findall(sample))
        if hits >= self.ABOUT_AUTHOR_THRESHOLD:
            return 0.8, "about_author"

        # Catalog (all-caps book titles)
        if self._re_catalog.search(text[:5000]):
            return 0.8, "catalog"

        return 0.0, ""

    # --- Signal 4: Prose density analysis ---

    def _score_density(self, text: str) -> float:
        """Score based on structural analysis of text density."""
        if not text or len(text) < 100:
            return 0.0

        lines = text.strip().split('\n')
        lines = [l for l in lines if l.strip()]

        if len(lines) < self.MIN_LINES_FOR_STRUCTURE:
            return 0.0

        total_chars = sum(len(l) for l in lines)
        if total_chars == 0:
            return 0.0

        signals = []

        # Numeric density
        digit_count = sum(1 for c in text if c.isdigit())
        numeric_density = digit_count / len(text)
        if numeric_density >= self.NUMERIC_DENSITY_HIGH:
            signals.append(0.8)
        elif numeric_density >= self.NUMERIC_DENSITY_LOW:
            signals.append(0.4)

        # Average line length (short lines = structural, not prose)
        avg_line_len = total_chars / len(lines)
        if avg_line_len < self.AVG_LINE_LENGTH_SHORT:
            signals.append(0.5)

        # Lines ending with numbers (index/toc pattern)
        number_endings = sum(1 for l in lines if l.strip() and l.strip()[-1].isdigit())
        number_ratio = number_endings / len(lines)
        if number_ratio >= self.NUMBER_ENDING_RATIO:
            signals.append(0.7)

        # Sentence density (prose has ~2+ sentences per 100 chars)
        sentence_ends = len(self._re_sentence_end.findall(text[:2000]))
        chars_sampled = min(len(text), 2000)
        sentence_density = (sentence_ends / chars_sampled) * 100 if chars_sampled > 0 else 0
        if sentence_density < self.SENTENCE_DENSITY_LOW:
            signals.append(0.3)

        # Comma-number sequences (index-like)
        comma_nums = len(self._re_comma_number.findall(text[:3000]))
        if comma_nums >= self.COMMA_NUMBER_SEQUENCES:
            signals.append(0.6)

        if not signals:
            return 0.0

        return sum(signals) / len(signals)

    # --- Combined scoring ---

    def classify(self, title: str = "", content: str = "",
                 epub_type: str = "", guide_type: str = "",
                 sensitivity: float = 0.5) -> ClassificationResult:
        """Classify a chapter as content or junk."""
        signals = {}
        categories = []

        # Signal 1: Title
        title_score, title_cat = self._score_title(title)
        if title_cat:
            categories.append(title_cat)

        # Content protection from title
        if title_score == -1.0:
            return ClassificationResult(
                is_junk=False, junk_score=0.0,
                signals={'title': 0.0}, category="content", confidence="high"
            )

        signals['title'] = max(0.0, title_score)

        # Signal 2: EPUB metadata
        epub_score = self._score_epub_metadata(epub_type, guide_type)
        if epub_score == -1.0:
            return ClassificationResult(
                is_junk=False, junk_score=0.0,
                signals={'title': signals.get('title', 0.0), 'epub': 0.0},
                category="content", confidence="high"
            )
        signals['epub'] = max(0.0, epub_score)

        # Signal 3: Content patterns
        pattern_score, pattern_cat = self._score_patterns(content)
        signals['patterns'] = pattern_score
        if pattern_cat:
            categories.append(pattern_cat)

        # Signal 4: Prose density
        density_score = self._score_density(content)
        signals['density'] = density_score

        # Weighted combination
        weights = {
            'title': self.WEIGHT_TITLE,
            'epub': self.WEIGHT_EPUB,
            'patterns': self.WEIGHT_PATTERNS,
            'density': self.WEIGHT_DENSITY,
        }

        # Only include signals that contributed
        active_weights = {k: v for k, v in weights.items() if signals.get(k, 0) > 0}
        total_weight = sum(active_weights.values()) if active_weights else 1.0

        if total_weight > 0 and active_weights:
            raw_score = sum(signals[k] * weights[k] for k in active_weights) / total_weight
        else:
            raw_score = 0.0

        # Multi-signal boost: if 2+ signals agree, boost score
        active_count = sum(1 for v in signals.values() if v > 0.3)
        if active_count >= 2:
            raw_score = min(1.0, raw_score * self.MULTI_SIGNAL_BOOST)

        # Apply sensitivity to threshold
        junk_threshold = self.BASE_JUNK_THRESHOLD - (sensitivity - 0.5) * 0.4
        junk_threshold = max(0.2, min(0.9, junk_threshold))

        suspect_threshold = self.BASE_SUSPECT_THRESHOLD - (sensitivity - 0.5) * 0.3
        suspect_threshold = max(0.1, min(0.7, suspect_threshold))

        # Determine classification
        is_junk = raw_score >= junk_threshold

        # Determine confidence
        if raw_score >= junk_threshold + 0.15:
            confidence = "high"
        elif raw_score >= junk_threshold:
            confidence = "medium"
        elif raw_score >= suspect_threshold:
            confidence = "low"
        else:
            confidence = "high"  # high confidence it's content

        # Pick best category
        category = categories[0] if categories else ("junk" if is_junk else "content")

        return ClassificationResult(
            is_junk=is_junk,
            junk_score=round(raw_score, 3),
            signals={k: round(v, 3) for k, v in signals.items()},
            category=category,
            confidence=confidence,
        )

    def classify_chapters(self, chapters: List[Dict], sensitivity: float = 0.5) -> List[ClassificationResult]:
        """Classify a list of chapter dicts."""
        results = []
        for ch in chapters:
            result = self.classify(
                title=ch.get('title', ''),
                content=ch.get('content', ''),
                epub_type=ch.get('epub_type', ''),
                guide_type=ch.get('guide_type', ''),
                sensitivity=sensitivity,
            )
            results.append(result)
        return results

    def find_content_boundaries(self, chapters: List[Dict],
                                 sensitivity: float = 0.5) -> Tuple[int, int]:
        """Find first and last content chapter indices.

        Returns (start_idx, end_idx) where end_idx is exclusive.
        Strips junk from front and back only.
        """
        results = self.classify_chapters(chapters, sensitivity)

        if not results:
            return 0, 0

        # Find first content chapter
        start_idx = 0
        for i, r in enumerate(results):
            if not r.is_junk:
                start_idx = i
                break
        else:
            # All junk? Return everything
            return 0, len(chapters)

        # Find last content chapter
        end_idx = len(chapters)
        for i in range(len(results) - 1, -1, -1):
            if not results[i].is_junk:
                end_idx = i + 1
                break

        return start_idx, end_idx

    def get_preview(self, chapter: Dict, max_sentences: int = 3) -> str:
        """Get heading + first N sentences of a chapter for preview."""
        title = chapter.get('title', '').strip()
        content = chapter.get('content', '').strip()

        if not content:
            return title if title else "(empty chapter)"

        # Extract first N sentences
        sentences = []
        current = []
        for char in content:
            current.append(char)
            if char in '.!?' and len(''.join(current).strip()) > 10:
                sentences.append(''.join(current).strip())
                current = []
                if len(sentences) >= max_sentences:
                    break

        # If no sentence boundaries found, take first 200 chars
        if not sentences:
            preview_text = content[:200].strip()
            if len(content) > 200:
                preview_text += "..."
        else:
            preview_text = ' '.join(sentences)

        if title:
            return f"{title}\n  {preview_text}"
        return preview_text
