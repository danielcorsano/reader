"""Tests for configuration management."""
import pytest
from pathlib import Path
from reader.config import ConfigManager, TTSConfig, AudioConfig, ProcessingConfig, AppConfig


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def config_manager(temp_config_dir):
    """Create ConfigManager with temp directory."""
    config_path = temp_config_dir / "settings.yaml"
    return ConfigManager(config_path)


def test_default_config_creation(config_manager):
    """Test default configuration is created correctly."""
    assert config_manager.config is not None
    assert isinstance(config_manager.config.tts, TTSConfig)
    assert isinstance(config_manager.config.audio, AudioConfig)
    assert isinstance(config_manager.config.processing, ProcessingConfig)


def test_default_tts_config(config_manager):
    """Test default TTS configuration values."""
    tts = config_manager.get_tts_config()
    assert tts.engine == "kokoro"
    assert tts.speed == 1.0
    assert tts.volume == 1.0


def test_default_audio_config(config_manager):
    """Test default audio configuration values."""
    audio = config_manager.get_audio_config()
    assert audio.format == "mp3"
    assert audio.add_metadata is True


def test_default_processing_config(config_manager):
    """Test default processing configuration values."""
    proc = config_manager.get_processing_config()
    assert proc.chunk_size == 400  # Optimal for Kokoro
    assert proc.level == "phase3"
    assert proc.character_voices is False  # Dialogue detection auto-enabled with character_voices


def test_save_and_load_config(config_manager):
    """Test saving and loading configuration."""
    # Modify config
    config_manager.update_tts_config(voice="test_voice", speed=1.5)

    # Create new manager with same path
    new_manager = ConfigManager(config_manager.config_path)

    # Verify loaded config matches
    assert new_manager.get_tts_config().voice == "test_voice"
    assert new_manager.get_tts_config().speed == 1.5


def test_update_tts_config(config_manager):
    """Test updating TTS configuration."""
    config_manager.update_tts_config(voice="new_voice", speed=1.2)

    tts = config_manager.get_tts_config()
    assert tts.voice == "new_voice"
    assert tts.speed == 1.2


def test_update_processing_config(config_manager):
    """Test updating processing configuration."""
    config_manager.update_processing_config(chunk_size=800)

    proc = config_manager.get_processing_config()
    assert proc.chunk_size == 800


def test_set_processing_level(config_manager):
    """Test setting processing level."""
    config_manager.set_processing_level("phase1")
    assert config_manager.get_processing_level() == "phase1"

    config_manager.set_processing_level("phase3")
    assert config_manager.get_processing_level() == "phase3"


def test_invalid_processing_level(config_manager):
    """Test invalid processing level raises error."""
    with pytest.raises(ValueError):
        config_manager.set_processing_level("invalid")


def test_phase_level_checks(config_manager):
    """Test phase level checking methods."""
    config_manager.set_processing_level("phase3")
    assert config_manager.is_phase3_enabled() is True
    assert config_manager.is_phase2_enabled() is True

    config_manager.set_processing_level("phase1")
    assert config_manager.is_phase3_enabled() is False
    assert config_manager.is_phase2_enabled() is False


def test_directory_paths(config_manager):
    """Test directory path getters."""
    text_dir = config_manager.get_text_dir()
    audio_dir = config_manager.get_audio_dir()
    config_dir = config_manager.get_config_dir()

    assert isinstance(text_dir, Path)
    assert isinstance(audio_dir, Path)
    assert isinstance(config_dir, Path)
