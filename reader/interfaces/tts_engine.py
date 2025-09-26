"""Abstract base class for TTS engines."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class TTSEngine(ABC):
    """Abstract base class for Text-to-Speech engines."""
    
    @abstractmethod
    def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None,
        speed: float = 1.0,
        volume: float = 1.0
    ) -> bytes:
        """
        Synthesize text to speech audio.
        
        Args:
            text: Text to synthesize
            voice: Voice identifier
            speed: Speech rate multiplier (1.0 = normal)
            volume: Volume multiplier (1.0 = normal)
            
        Returns:
            Audio data as bytes
        """
        pass
    
    @abstractmethod
    def list_voices(self) -> List[str]:
        """
        Get list of available voice identifiers.
        
        Returns:
            List of voice names/IDs
        """
        pass
    
    @abstractmethod
    def save_audio(
        self, 
        audio_data: bytes, 
        output_path: Path,
        format: str = "wav"
    ) -> None:
        """
        Save audio data to file.
        
        Args:
            audio_data: Audio bytes to save
            output_path: Output file path
            format: Audio format (wav, mp3, etc.)
        """
        pass
    
    @abstractmethod
    def get_voice_info(self, voice: str) -> Dict[str, Any]:
        """
        Get information about a specific voice.
        
        Args:
            voice: Voice identifier
            
        Returns:
            Dictionary with voice metadata
        """
        pass