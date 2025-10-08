"""Tests for text parsers."""
import pytest
from pathlib import Path
from reader.parsers.epub_parser import EPUBParser
from reader.parsers.pdf_parser import PDFParser
from reader.parsers.text_parser import PlainTextParser


@pytest.fixture
def epub_parser():
    """Create EPUB parser instance."""
    return EPUBParser()


@pytest.fixture
def pdf_parser():
    """Create PDF parser instance."""
    return PDFParser()


@pytest.fixture
def text_parser():
    """Create text parser instance."""
    return PlainTextParser()


def test_epub_parser_can_parse(epub_parser):
    """Test EPUB parser file detection."""
    assert epub_parser.can_parse(Path("book.epub"))
    assert epub_parser.can_parse(Path("book.EPUB"))
    assert not epub_parser.can_parse(Path("book.pdf"))
    assert not epub_parser.can_parse(Path("book.txt"))


def test_pdf_parser_can_parse(pdf_parser):
    """Test PDF parser file detection."""
    assert pdf_parser.can_parse(Path("book.pdf"))
    assert pdf_parser.can_parse(Path("book.PDF"))
    assert not pdf_parser.can_parse(Path("book.epub"))
    assert not pdf_parser.can_parse(Path("book.txt"))


def test_text_parser_can_parse(text_parser):
    """Test text parser file detection."""
    assert text_parser.can_parse(Path("book.txt"))
    assert text_parser.can_parse(Path("book.TXT"))
    assert text_parser.can_parse(Path("book.md"))
    assert text_parser.can_parse(Path("book.rst"))
    assert not text_parser.can_parse(Path("book.epub"))
    assert not text_parser.can_parse(Path("book.pdf"))


def test_epub_parser_extensions(epub_parser):
    """Test EPUB parser supported extensions."""
    assert ".epub" in epub_parser.get_supported_extensions()


def test_pdf_parser_extensions(pdf_parser):
    """Test PDF parser supported extensions."""
    assert ".pdf" in pdf_parser.get_supported_extensions()


def test_text_parser_extensions(text_parser):
    """Test text parser supported extensions."""
    extensions = text_parser.get_supported_extensions()
    assert ".txt" in extensions
    assert ".md" in extensions


def test_text_parser_basic_parsing(text_parser, tmp_path):
    """Test basic text file parsing."""
    test_file = tmp_path / "test.txt"
    test_content = "This is a test.\n\nSecond paragraph."
    test_file.write_text(test_content)

    result = text_parser.parse(test_file)
    assert result.content == test_content
    assert result.title == 'test'
    assert result.metadata['title'] == 'test'


def test_text_parser_invalid_file(text_parser):
    """Test text parser with non-existent file."""
    with pytest.raises(Exception):
        text_parser.parse(Path("nonexistent.txt"))
