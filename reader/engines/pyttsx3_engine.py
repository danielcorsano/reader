"""pyttsx3 TTS engine implementation."""
import pyttsx3
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile

from ..interfaces.tts_engine import TTSEngine


class PyTTSX3Engine(TTSEngine):
    """TTS engine implementation using pyttsx3."""
    
    def __init__(self):
        """Initialize the pyttsx3 engine."""
        self.engine = pyttsx3.init()
        self._temp_file = None
    
    def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None,
        speed: float = 1.0,
        volume: float = 1.0
    ) -> bytes:
        """
        Synthesize text to speech audio using pyttsx3.
        
        Args:
            text: Text to synthesize
            voice: Voice identifier (system voice name)
            speed: Speech rate multiplier
            volume: Volume multiplier
            
        Returns:
            Audio data as bytes (WAV format)
        """
        # Set voice if specified
        if voice:
            voices = self.engine.getProperty('voices')
            for v in voices:
                if voice.lower() in v.name.lower() or voice == v.id:
                    self.engine.setProperty('voice', v.id)
                    break
        
        # Set speech rate (pyttsx3 uses words per minute)
        base_rate = self.engine.getProperty('rate')
        self.engine.setProperty('rate', int(base_rate * speed))
        
        # Set volume (0.0 to 1.0)
        self.engine.setProperty('volume', min(1.0, max(0.0, volume)))
        
        # Create temporary file for audio output
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save to file (pyttsx3 doesn't support direct byte output)
            self.engine.save_to_file(text, temp_path)
            self.engine.runAndWait()
            
            # Read the file back as bytes
            with open(temp_path, 'rb') as f:
                audio_bytes = f.read()
            
            return audio_bytes
            
        finally:
            # Clean up temporary file
            try:
                Path(temp_path).unlink()
            except:
                pass
    
    def list_voices(self) -> List[str]:
        """
        Get list of available system voices.
        
        Returns:
            List of voice names
        """
        voices = self.engine.getProperty('voices')
        return [voice.name for voice in voices if voice.name]
    
    def save_audio(
        self, 
        audio_data: bytes, 
        output_path: Path,
        format: str = "wav"
    ) -> None:
        """
        Save audio data to file with format conversion support.
        
        Args:
            audio_data: Audio bytes to save
            output_path: Output file path
            format: Target audio format
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to use Phase 3 audio processor for format conversion
        try:
            from ..processors.ffmpeg_processor import get_audio_processor
            audio_processor = get_audio_processor()
            
            if format.lower() != "wav":
                # Save as temporary WAV first
                temp_wav = output_path.with_suffix('.wav')
                with open(temp_wav, 'wb') as f:
                    f.write(audio_data)
                
                # Convert to target format
                final_output = output_path.with_suffix(f'.{format.lower()}')
                audio_processor.convert_format(temp_wav, final_output, format)
                
                # Clean up temp file
                temp_wav.unlink(missing_ok=True)
                return
            
        except ImportError:
            # Phase 3 not available, fallback to WAV only
            if format.lower() != "wav":
                print(f"Warning: Format conversion requires Phase 3. Saving as WAV instead.")
                output_path = output_path.with_suffix('.wav')
        
        # Direct save for WAV or fallback
        with open(output_path, 'wb') as f:
            f.write(audio_data)
    
    def get_voice_info(self, voice: str) -> Dict[str, Any]:
        """
        Get information about a specific voice.
        
        Args:
            voice: Voice identifier
            
        Returns:
            Dictionary with voice metadata
        """
        voices = self.engine.getProperty('voices')
        
        for v in voices:
            if voice.lower() in v.name.lower() or voice == v.id:
                return {
                    'id': v.id,
                    'name': v.name,
                    'languages': getattr(v, 'languages', []),
                    'gender': getattr(v, 'gender', 'unknown'),
                    'age': getattr(v, 'age', 'unknown')
                }
        
        return {
            'id': voice,
            'name': voice,
            'languages': [],
            'gender': 'unknown',
            'age': 'unknown',
            'found': False
        }
    
    def get_default_voice(self) -> str:
        """Get the current default voice."""
        current_voice_id = self.engine.getProperty('voice')
        voices = self.engine.getProperty('voices')
        
        for voice in voices:
            if voice.id == current_voice_id:
                return voice.name
        
        return "Default"
    
    def set_properties(self, **kwargs) -> None:
        """Set engine properties directly."""
        for prop, value in kwargs.items():
            if prop in ['rate', 'volume', 'voice']:
                self.engine.setProperty(prop, value)