"""Configuration management for the reader application."""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TTSConfig:
    """TTS engine configuration."""
    engine: str = "kokoro"  # Default to Neural Engine for best performance
    voice: Optional[str] = None
    speed: float = 1.0
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
    character_voices: bool = False  # Off by default
    dialogue_detection: bool = True
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


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager."""
        if config_path is None:
            config_path = Path.cwd() / "config" / "settings.yaml"

        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or create default config
        config_exists = self.config_path.exists()
        self.config = self.load_config()

        # Save default config file if it doesn't exist (makes it discoverable/editable)
        if not config_exists:
            self.save_config()
    
    def load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Convert dict to config objects with backward compatibility
                tts_data = config_data.get('tts', {})
                # Remove old fields that no longer exist
                tts_data = {k: v for k, v in tts_data.items() if k in ['engine', 'voice', 'speed', 'volume']}
                
                audio_data = config_data.get('audio', {})
                # Remove old fields that no longer exist  
                audio_data = {k: v for k, v in audio_data.items() if k in ['format', 'add_metadata']}
                
                processing_data = config_data.get('processing', {})
                # Remove old fields that no longer exist
                valid_fields = ['chunk_size', 'pause_between_chapters', 'auto_detect_chapters', 'level',
                               'character_voices', 'dialogue_detection', 'chapter_metadata', 'batch_processing']
                processing_data = {k: v for k, v in processing_data.items() if k in valid_fields}
                
                return AppConfig(
                    tts=TTSConfig(**tts_data),
                    audio=AudioConfig(**audio_data),
                    processing=ProcessingConfig(**processing_data),
                    text_dir=config_data.get('text_dir', 'text'),
                    audio_dir=config_data.get('audio_dir', 'audio'),
                    config_dir=config_data.get('config_dir', 'config'),
                    output_dir=config_data.get('output_dir', 'downloads')
                )
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                print("Using default configuration.")
        
        # Return default config
        return AppConfig(
            tts=TTSConfig(),
            audio=AudioConfig(),
            processing=ProcessingConfig()
        )
    
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
            self.config.processing.dialogue_detection = False
        elif level == "phase2":
            self.config.processing.character_voices = False
            self.config.processing.dialogue_detection = False
        elif level == "phase3":
            self.config.processing.character_voices = False
            self.config.processing.dialogue_detection = True
        
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