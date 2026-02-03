"""Configuration management for the reader application."""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from copy import deepcopy


@dataclass
class TTSConfig:
    """TTS engine configuration."""
    engine: str = "kokoro"  # Default to Neural Engine for best performance
    voice: Optional[str] = None
    speed: float = 1.1
    volume: float = 1.0


@dataclass
class AudioConfig:
    """Audio output configuration."""
    format: str = "mp3"  # Optimized mono MP3 for audiobooks
    bitrate: str = "48k"  # MP3 bitrate (32k-64k typical for audiobooks)
    add_metadata: bool = True


@dataclass
class ProcessingConfig:
    """Text processing configuration."""
    chunk_size: int = 400  # Optimal for Kokoro (450 char limit, 400 recommended)
    pause_between_chapters: float = 1.0
    auto_detect_chapters: bool = True
    level: str = "phase3"  # Use all available features by default
    character_voices: bool = False  # Off by default (dialogue detection auto-enabled when enabled)
    chapter_metadata: bool = True
    batch_processing: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    tts: TTSConfig
    audio: AudioConfig
    processing: ProcessingConfig
    text_dir: str = "text"
    audio_dir: str = "audio"
    config_dir: str = "config"
    output_dir: str = "downloads"
    ffmpeg_path: Optional[str] = None  # Custom FFmpeg path (uses PATH if None)
    models_dir: Optional[str] = None  # Custom models directory (uses cache if None)


def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    """Deep merge update dict into base dict (modifies base in place)."""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager with multi-layer config hierarchy.

        Hierarchy (priority low → high):
        1. Defaults (dataclass defaults)
        2. User config (~/.config/audiobook-reader/config.yaml)
        3. Project config (.reader.yaml - loaded per-file via load_file_config)
        4. CLI overrides (via override method)
        """
        # Use standard user config location
        if config_path is None:
            config_path = Path.home() / ".config" / "audiobook-reader" / "config.yaml"

        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Start with defaults
        self.config = AppConfig(
            tts=TTSConfig(),
            audio=AudioConfig(),
            processing=ProcessingConfig()
        )

        # Load user config if exists
        if self.config_path.exists():
            self._load_and_merge_config(self.config_path)

    def _load_and_merge_config(self, config_file: Path) -> None:
        """Load YAML config and merge into current config."""
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}

            # Convert current config to dict, merge, convert back
            current_dict = asdict(self.config)
            _deep_merge(current_dict, config_data)
            self._update_config_from_dict(current_dict)
        except Exception as e:
            print(f"Warning: Could not load config from {config_file}: {e}")

    def _update_config_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update config dataclasses from dict (with backward compatibility)."""
        # TTS config
        tts_data = config_dict.get('tts', {})
        tts_data = {k: v for k, v in tts_data.items() if k in ['engine', 'voice', 'speed', 'volume']}
        for key, value in tts_data.items():
            if hasattr(self.config.tts, key):
                setattr(self.config.tts, key, value)

        # Audio config
        audio_data = config_dict.get('audio', {})
        audio_data = {k: v for k, v in audio_data.items() if k in ['format', 'bitrate', 'add_metadata']}
        for key, value in audio_data.items():
            if hasattr(self.config.audio, key):
                setattr(self.config.audio, key, value)

        # Processing config
        processing_data = config_dict.get('processing', {})
        valid_fields = ['chunk_size', 'pause_between_chapters', 'auto_detect_chapters', 'level',
                       'character_voices', 'chapter_metadata', 'batch_processing']
        processing_data = {k: v for k, v in processing_data.items() if k in valid_fields}
        for key, value in processing_data.items():
            if hasattr(self.config.processing, key):
                setattr(self.config.processing, key, value)

        # Top-level config
        for key in ['text_dir', 'audio_dir', 'config_dir', 'output_dir', 'ffmpeg_path', 'models_dir']:
            if key in config_dict:
                setattr(self.config, key, config_dict[key])

    def find_local_config(self, file_path: Path) -> Optional[Path]:
        """Find project config (.reader.yaml) searching upward from file's directory.

        Args:
            file_path: Path to the file being converted

        Returns:
            Path to config file if found, None otherwise
        """
        search_dir = file_path.parent.resolve()
        home_dir = Path.home()

        # Search up through parent directories
        while True:
            # Try multiple config file names
            for config_name in ['.reader.yaml', 'audiobook-reader.yaml']:
                config_path = search_dir / config_name
                if config_path.exists():
                    return config_path

            # Stop at home directory (don't go to root)
            if search_dir == home_dir or search_dir.parent == search_dir:
                break

            search_dir = search_dir.parent

        return None

    def load_file_config(self, file_path: Path) -> None:
        """Load and merge project-specific config for a file.

        Searches for .reader.yaml or audiobook-reader.yaml from file's directory
        up to home directory. Project config overrides user config.

        Args:
            file_path: Path to the file being converted
        """
        local_config = self.find_local_config(file_path)
        if local_config:
            self._load_and_merge_config(local_config)

    def save_config(self) -> None:
        """Save current configuration to file."""
        config_dict = asdict(self.config)
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config to {self.config_path}: {e}")
    
    def get_tts_config(self) -> TTSConfig:
        """Get TTS configuration."""
        return self.config.tts
    
    def get_audio_config(self) -> AudioConfig:
        """Get audio configuration."""
        return self.config.audio
    
    def get_processing_config(self) -> ProcessingConfig:
        """Get processing configuration."""
        return self.config.processing
    
    def update_tts_config(self, **kwargs) -> None:
        """Update TTS configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config.tts, key):
                setattr(self.config.tts, key, value)
        self.save_config()
    
    def update_audio_config(self, **kwargs) -> None:
        """Update audio configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config.audio, key):
                setattr(self.config.audio, key, value)
        self.save_config()
    
    def update_processing_config(self, **kwargs) -> None:
        """Update processing configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config.processing, key):
                setattr(self.config.processing, key, value)
        self.save_config()
    
    def set_processing_level(self, level: str) -> None:
        """Set processing level (phase1, phase2, phase3)."""
        valid_levels = ["phase1", "phase2", "phase3"]
        if level not in valid_levels:
            raise ValueError(f"Invalid processing level. Must be one of: {valid_levels}")
        
        self.config.processing.level = level
        
        # Auto-configure features based on level
        # All levels use kokoro now (pyttsx3 moved to reader-small)
        self.config.tts.engine = "kokoro"

        if level == "phase1":
            self.config.processing.character_voices = False
        elif level == "phase2":
            self.config.processing.character_voices = False
        elif level == "phase3":
            self.config.processing.character_voices = False
        
        self.save_config()
    
    def get_processing_level(self) -> str:
        """Get current processing level."""
        return self.config.processing.level
    
    def is_phase2_enabled(self) -> bool:
        """Check if Phase 2 features are enabled."""
        return self.config.processing.level in ["phase2", "phase3"]
    
    def is_phase3_enabled(self) -> bool:
        """Check if Phase 3 features are enabled."""
        return self.config.processing.level == "phase3"
    
    def get_text_dir(self) -> Path:
        """Get text input directory path."""
        return Path(self.config.text_dir)
    
    def get_audio_dir(self) -> Path:
        """Get audio output directory path."""
        return Path(self.config.audio_dir)
    
    def get_config_dir(self) -> Path:
        """Get configuration directory path."""
        return Path(self.config.config_dir)

    def get_output_dir(self, source_file: Path = None) -> Path:
        """Get output directory path based on configuration.

        Args:
            source_file: Source file path (used when output_dir is 'same')

        Returns:
            Resolved output directory path
        """
        output_dir_config = self.config.output_dir

        if output_dir_config == "downloads":
            return Path.home() / "Downloads"
        elif output_dir_config == "same" and source_file:
            return source_file.parent
        elif output_dir_config == "same":
            # Fallback if no source file provided
            return Path.cwd()
        else:
            # Treat as explicit path
            return Path(output_dir_config)

    def list_available_voices(self) -> Dict[str, Any]:
        """Get available voices from TTS engines."""
        # This will be populated by the TTS engines
        voices_file = self.get_config_dir() / "available_voices.yaml"
        
        if voices_file.exists():
            try:
                with open(voices_file, 'r') as f:
                    return yaml.safe_load(f)
            except:
                pass
        
        return {}