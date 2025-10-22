"""Tests for TTS engines."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from reader.engines.kokoro_engine import KokoroEngine, KOKORO_AVAILABLE


@pytest.fixture
def mock_kokoro():
    """Mock Kokoro TTS instance."""
    with patch('reader.engines.kokoro_engine.Kokoro') as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


def test_kokoro_voices_defined():
    """Test Kokoro engine has voice definitions."""
    assert len(KokoroEngine.VOICES) > 0
    assert "am_michael" in KokoroEngine.VOICES
    assert "af_sarah" in KokoroEngine.VOICES


def test_kokoro_voice_metadata():
    """Test Kokoro voice metadata structure."""
    for voice_id, voice_data in KokoroEngine.VOICES.items():
        assert "name" in voice_data
        assert "lang" in voice_data
        assert "gender" in voice_data
        assert voice_data["gender"] in ["male", "female"]


def test_kokoro_voice_languages():
    """Test Kokoro voices have correct language codes."""
    voice_data = KokoroEngine.VOICES

# Check American English voices
    assert voice_data["am_michael"]["lang"] == "en-us"
    assert voice_data["af_sarah"]["lang"] == "en-us"

    # Check British English voices
    assert voice_data["bm_george"]["lang"] == "en-gb"
    assert voice_data["bf_emma"]["lang"] == "en-gb"


@pytest.mark.skipif(not KOKORO_AVAILABLE, reason="Kokoro not installed")
def test_kokoro_initialization_without_models():
    """Test Kokoro initialization fails gracefully without models."""
    engine = KokoroEngine()
    assert engine is not None


def test_kokoro_sentence_pattern():
    """Test sentence splitting pattern."""
    pattern = KokoroEngine.SENTENCE_SPLIT_PATTERN
    text = "First sentence. Second sentence! Third sentence?"
    parts = pattern.split(text)
    assert len(parts) == 3


def test_kokoro_punctuation_pattern():
    """Test punctuation splitting pattern."""
    pattern = KokoroEngine.PUNCTUATION_SPLIT_PATTERN
    text = "Hello, world"
    result = pattern.split(text)
    assert "," in result


def test_kokoro_not_available_error():
    """Test error when Kokoro not available."""
    with patch('reader.engines.kokoro_engine.KOKORO_AVAILABLE', False):
        with pytest.raises(ImportError):
            KokoroEngine()
