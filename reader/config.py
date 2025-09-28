"""Configuration management for the reader application."""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TTSConfig:
    """TTS engine configuration."""
    engine: str = "pyttsx3"  # "pyttsx3" or "kokoro"
    voice: Optional[str] = None
    speed: float = 0.9
    volume: float = 1.0
    # Phase 2 options
    fallback_engine: str = "pyttsx3"  # Fallback if primary engine fails
    fallback_voice: str = "af_sarah"  # Default voice when engine fails to auto-assign


@dataclass
class AudioConfig:
    """Audio output configuration."""
    format: str = "wav"  # Phase 1-2 support WAV, Phase 3+ adds MP3/M4B
    add_metadata: bool = False  # Phase 3+ feature


@dataclass
class ProcessingConfig:
    """Text processing configuration."""
    chunk_size: int = 1000
    pause_between_chapters: float = 1.0
    auto_detect_chapters: bool = True
    # Phase selection
    level: str = "phase1"  # "phase1", "phase2", "phase3"
    # Phase 2 options
    emotion_analysis: bool = True
    smart_acting: bool = True
    character_voices: bool = True
    voice_blending: bool = False  # Advanced feature
    # Phase 3 options
    dialogue_detection: bool = True
    advanced_audio_formats: bool = True
    chapter_metadata: bool = True
    voice_preview: bool = True
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


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager."""
        if config_path is None:
            config_path = Path.cwd() / "config" / "settings.yaml"
        
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or create default config
        self.config = self.load_config()
    
    def load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Convert dict to config objects
                return AppConfig(
                    tts=TTSConfig(**config_data.get('tts', {})),
                    audio=AudioConfig(**config_data.get('audio', {})),
                    processing=ProcessingConfig(**config_data.get('processing', {})),
                    text_dir=config_data.get('text_dir', 'text'),
                    audio_dir=config_data.get('audio_dir', 'audio'),
                    config_dir=config_data.get('config_dir', 'config')
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
        if level == "phase1":
            self.config.processing.emotion_analysis = False
            self.config.processing.character_voices = False
            self.config.processing.dialogue_detection = False
            self.config.processing.advanced_audio_formats = False
            self.config.tts.engine = "pyttsx3"
        elif level == "phase2":
            self.config.processing.emotion_analysis = True
            self.config.processing.character_voices = True
            self.config.processing.dialogue_detection = False
            self.config.processing.advanced_audio_formats = False
            # Only set to kokoro if it's likely to work
            try:
                from ..engines.kokoro_engine import KokoroEngine
                # Test if we can initialize without models
                self.config.tts.engine = "kokoro"
            except:
                self.config.tts.engine = "pyttsx3"
        elif level == "phase3":
            self.config.processing.emotion_analysis = True
            self.config.processing.character_voices = True
            self.config.processing.dialogue_detection = True
            self.config.processing.advanced_audio_formats = True
            # Only set to kokoro if it's likely to work
            try:
                from ..engines.kokoro_engine import KokoroEngine
                # Test if we can initialize without models
                self.config.tts.engine = "kokoro"
            except:
                self.config.tts.engine = "pyttsx3"
        
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