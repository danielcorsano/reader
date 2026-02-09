"""Tests for HeadingDetector — covers all 3 tiers and edge cases."""
from reader.text_processing.heading_detector import HeadingDetector


def test_tier1_marked_chapters_pass_through():
    """Real titles pass through unchanged."""
    hd = HeadingDetector()
    chapters = [
        {'title': 'Introduction', 'content': 'text'},
        {'title': 'Chapter 1', 'content': 'more text'},
    ]
    result = hd.detect("ignored", chapters=chapters)
    assert result == chapters


def test_tier1_page_based_falls_through():
    """Page-numbered chapters trigger heading detection."""
    hd = HeadingDetector()
    text = "\n\nChapter I\n\nSome content here.\n\nChapter II\n\nMore content here.\n\n"
    pages = [{'title': 'Page 1', 'content': ''}, {'title': 'Page 2', 'content': ''}]
    result = hd.detect(text, chapters=pages)
    assert len(result) >= 2
    assert 'Chapter I' in result[0]['title']


def test_tier2_known_sections():
    hd = HeadingDetector()
    text = "\n\nPrologue\n\nOnce upon a time.\n\nChapter I\n\nThe story begins.\n\nEpilogue\n\nThe end.\n\n"
    result = hd.detect(text)
    titles = [ch['title'] for ch in result]
    assert 'Prologue' in titles
    assert 'Epilogue' in titles


def test_tier2_isolated_title_lines():
    """Short isolated lines with blank before/after are detected as headings."""
    hd = HeadingDetector()
    text = "\n\nThe Beginning\n\nContent of first section goes here and continues.\n\nThe Middle\n\nMore content follows.\n\n"
    result = hd.detect(text)
    assert len(result) >= 2


def test_tier3_all_caps():
    hd = HeadingDetector()
    text = "\n\nFIRST SECTION\n\nSome content about the first topic that goes on.\n\nSECOND SECTION\n\nAnother section with more content.\n\n"
    result = hd.detect(text)
    assert len(result) >= 2
    assert any('FIRST' in ch['title'] for ch in result)


def test_noise_filtering():
    """Bare numbers and numbered paragraphs are not headings."""
    hd = HeadingDetector()
    lines = ['42', '1. this is a paragraph', 'Chapter I']
    assert hd._is_noise('42')
    assert hd._is_noise('1. this is a paragraph')
    assert not hd._is_noise('Chapter I')


def test_empty_text_returns_empty():
    hd = HeadingDetector()
    assert hd.detect("") == []
    assert hd.detect("Short text with no structure.") == []


def test_split_preserves_content():
    hd = HeadingDetector()
    text = "\n\nIntroduction\n\nFirst paragraph.\nSecond paragraph.\n\nChapter I\n\nThird paragraph.\n\n"
    result = hd.detect(text)
    all_content = ' '.join(ch['content'] for ch in result)
    assert 'First paragraph' in all_content
    assert 'Third paragraph' in all_content
