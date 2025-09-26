"""Configuration management for the reader application."""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TTSConfig:
    """TTS engine configuration."""
    engine: str = "pyttsx3"
    voice: Optional[str] = None
    speed: float = 1.0
    volume: float = 1.0


@dataclass
class AudioConfig:
    """Audio output configuration."""
    format: str = "wav"  # Phase 1 only supports WAV
    add_metadata: bool = False  # Phase 1 doesn't support metadata


@dataclass
class ProcessingConfig:
    """Text processing configuration."""
    chunk_size: int = 1000
    pause_between_chapters: float = 1.0
    auto_detect_chapters: bool = True


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