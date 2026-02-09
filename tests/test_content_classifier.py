"""Tests for ContentClassifier — covers all 5 signals, boundaries, and edge cases."""
from reader.text_processing.content_classifier import ContentClassifier


def make_chapters(specs):
    """Build chapter dicts from (title, content_len) tuples."""
    return [{'title': t, 'content': 'x' * n} for t, n in specs]


def test_title_signal_junk():
    c = ContentClassifier()
    r = c.classify(title="Copyright")
    assert r.signals['title'] > 0.5
    assert r.category == "copyright"


def test_title_signal_content_protection():
    """Numbered chapters are protected from false positives."""
    c = ContentClassifier()
    r = c.classify(title="Chapter 5: The Journey")
    assert not r.is_junk
    assert r.junk_score == 0.0


def test_epub_metadata_signal():
    c = ContentClassifier()
    r = c.classify(epub_type="copyright-page")
    assert r.signals['epub'] > 0.5


def test_epub_metadata_content_protection():
    c = ContentClassifier()
    r = c.classify(epub_type="bodymatter")
    assert not r.is_junk


def test_pattern_signal_copyright():
    text = "Copyright 2024. All rights reserved. ISBN 978-0-123456-78-9. Published by Example Press."
    c = ContentClassifier()
    r = c.classify(content=text)
    assert r.signals['patterns'] > 0.3


def test_density_signal_short_content():
    c = ContentClassifier()
    r = c.classify(content="Very short.")
    assert r.signals['density'] > 0.3


def test_density_signal_prose():
    """Long prose should not flag density."""
    prose = "This is a sentence about the nature of existence. " * 40
    c = ContentClassifier()
    r = c.classify(content=prose)
    assert r.signals['density'] <= 0.3


def test_relative_length_signal():
    chapters = make_chapters([
        ("Ch 1", 5000), ("Ch 2", 4800), ("Ch 3", 5200),
        ("Copyright", 100),
    ])
    c = ContentClassifier()
    c.set_context(chapters)
    assert c._score_relative_length(100) == 0.9  # <10% of median
    assert c._score_relative_length(800) == 0.7  # <20%
    assert c._score_relative_length(1500) == 0.4  # <35%
    assert c._score_relative_length(4000) == 0.0  # normal


def test_relative_length_no_context():
    """Without set_context, length signal returns 0 (safe default)."""
    c = ContentClassifier()
    assert c._score_relative_length(50) == 0.0


def test_classify_junk_multi_signal():
    """Copyright title + copyright patterns + short = junk."""
    c = ContentClassifier()
    r = c.classify(title="Copyright Page", content="Copyright 2024. All rights reserved. Published by X.")
    assert r.is_junk


def test_classify_real_chapter():
    prose = "The morning sun cast long shadows across the valley. " * 30
    c = ContentClassifier()
    r = c.classify(title="Chapter 1", content=prose)
    assert not r.is_junk
    assert r.category == "content"


def test_find_content_boundaries():
    chapters = [
        {'title': 'Copyright', 'content': 'Copyright 2024. All rights reserved.'},
        {'title': 'Also By', 'content': 'Other books by author.'},
        {'title': 'Chapter 1', 'content': 'The story begins. ' * 50},
        {'title': 'Chapter 2', 'content': 'It continued on. ' * 50},
        {'title': 'Index', 'content': 'Alpha, 1, 5\nBeta, 2, 8\nGamma, 3, 12\n' * 5},
    ]
    c = ContentClassifier()
    c.set_context(chapters)
    start, end = c.find_content_boundaries(chapters, sensitivity=0.6)
    assert start >= 1  # skips copyright/also-by
    assert end <= 4    # skips index


def test_classify_chapters_batch():
    chapters = [
        {'title': 'Index', 'content': 'Alpha, 1\nBeta, 2\n' * 10},
        {'title': 'Chapter 1', 'content': 'Narrative text. ' * 40},
    ]
    c = ContentClassifier()
    results = c.classify_chapters(chapters)
    assert len(results) == 2
    assert results[1].category == "content"
