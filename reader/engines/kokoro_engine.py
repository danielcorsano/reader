"""Kokoro TTS engine implementation with voice blending."""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import warnings

from ..interfaces.tts_engine import TTSEngine

try:
    from kokoro_onnx import Kokoro
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False
    warnings.warn("Kokoro ONNX not available. Install with: poetry add kokoro-onnx")


class KokoroEngine(TTSEngine):
    """TTS engine implementation using Kokoro ONNX."""
    
    # Kokoro voice mappings with language codes
    VOICES = {
        # American English
        "af_sarah": {"name": "Sarah (American)", "lang": "en-us", "gender": "female"},
        "af_nicole": {"name": "Nicole (American)", "lang": "en-us", "gender": "female"},
        "af_michael": {"name": "Michael (American)", "lang": "en-us", "gender": "male"},
        "af_adam": {"name": "Adam (American)", "lang": "en-us", "gender": "male"},
        
        # British English  
        "bf_emma": {"name": "Emma (British)", "lang": "en-uk", "gender": "female"},
        "bf_isabella": {"name": "Isabella (British)", "lang": "en-uk", "gender": "female"},
        "bf_oliver": {"name": "Oliver (British)", "lang": "en-uk", "gender": "male"},
        "bf_william": {"name": "William (British)", "lang": "en-uk", "gender": "male"},
        
        # Other languages (examples)
        "ef_clara": {"name": "Clara (Spanish)", "lang": "es", "gender": "female"},
        "ef_pedro": {"name": "Pedro (Spanish)", "lang": "es", "gender": "male"},
        "ff_marie": {"name": "Marie (French)", "lang": "fr", "gender": "female"},
        "ff_pierre": {"name": "Pierre (French)", "lang": "fr", "gender": "male"},
    }
    
    def __init__(self):
        """Initialize the Kokoro engine."""
        if not KOKORO_AVAILABLE:
            raise ImportError("Kokoro ONNX not available. Install with: poetry add kokoro-onnx")
        
        self.kokoro = None
        self._initialized = False
        self._init_error = None
    
    def _ensure_initialized(self) -> None:
        """Ensure Kokoro is initialized, initializing lazily if needed."""
        if self._initialized:
            if self.kokoro is None:
                raise RuntimeError(f"Kokoro initialization failed: {self._init_error}")
            return
            
        try:
            # Initialize with proper model paths
            model_path = Path(__file__).parent.parent.parent / "models" / "kokoro" / "kokoro-v1.0.onnx"
            voices_path = Path(__file__).parent.parent.parent / "models" / "kokoro" / "voices-v1.0.bin"
            
            if not model_path.exists() or not voices_path.exists():
                raise FileNotFoundError(f"Kokoro models not found. Please download:\n"
                                      f"  {model_path}\n"
                                      f"  {voices_path}\n"
                                      f"See docs/KOKORO_SETUP.md for instructions")
            
            self.kokoro = Kokoro(str(model_path), str(voices_path))
            self._initialized = True
            
        except Exception as e:
            self._initialized = True
            self._init_error = str(e)
            self.kokoro = None
            raise RuntimeError(f"Failed to initialize Kokoro: {e}")
    
    def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None,
        speed: float = 1.0,
        volume: float = 1.0
    ) -> bytes:
        """
        Synthesize text to speech using Kokoro.
        
        Args:
            text: Text to synthesize
            voice: Voice identifier or blend (e.g., "af_sarah" or "af_sarah:60,af_nicole:40")
            speed: Speech rate multiplier
            volume: Volume multiplier (not directly supported by Kokoro)
            
        Returns:
            Audio data as bytes (WAV format)
        """
        self._ensure_initialized()
        if not self.kokoro:
            raise RuntimeError("Kokoro engine not initialized")
        
        # Default voice
        if not voice:
            voice = "af_sarah"
        
        # Handle voice blending
        voice_blend = self._parse_voice_blend(voice)
        
        try:
            # Generate audio with Kokoro
            if len(voice_blend) == 1:
                # Single voice
                voice_id, _ = list(voice_blend.items())[0]
                samples, sample_rate = self.kokoro.create(
                    text=text,
                    voice=voice_id,
                    speed=speed,
                    lang=self._get_voice_lang(voice_id)
                )
            else:
                # Voice blending - use primary voice (highest weight)
                primary_voice = max(voice_blend.items(), key=lambda x: x[1])[0]
                samples, sample_rate = self.kokoro.create(
                    text=text,
                    voice=primary_voice,
                    speed=speed,
                    lang=self._get_voice_lang(primary_voice)
                )
            
            # Convert to WAV bytes
            return self._samples_to_wav_bytes(samples, sample_rate)
            
        except Exception as e:
            raise RuntimeError(f"Kokoro synthesis failed: {e}")
    
    def list_voices(self) -> List[str]:
        """Get list of available Kokoro voices."""
        try:
            self._ensure_initialized()
            if self.kokoro and hasattr(self.kokoro, 'get_voices'):
                return self.kokoro.get_voices()
            else:
                # Fallback to static voice list
                return list(self.VOICES.keys())
        except:
            # Fallback to static voice list if initialization fails
            return list(self.VOICES.keys())
    
    def save_audio(
        self, 
        audio_data: bytes, 
        output_path: Path,
        format: str = "wav"
    ) -> None:
        """Save audio data to file with format conversion support."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to use Phase 3 audio processor for format conversion
        try:
            from ..audio.ffmpeg_processor import get_audio_processor
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
        """Get information about a specific voice."""
        if voice in self.VOICES:
            info = self.VOICES[voice].copy()
            info['engine'] = 'kokoro'
            info['found'] = True
            return info
        
        return {
            'id': voice,
            'name': voice,
            'engine': 'kokoro',
            'found': False
        }
    
    def _parse_voice_blend(self, voice_spec: str) -> Dict[str, float]:
        """
        Parse voice blend specification.
        
        Examples:
            "af_sarah" -> {"af_sarah": 1.0}
            "af_sarah:60,af_nicole:40" -> {"af_sarah": 0.6, "af_nicole": 0.4}
        """
        if ':' not in voice_spec:
            return {voice_spec: 1.0}
        
        blend = {}
        total_weight = 0
        
        for voice_weight in voice_spec.split(','):
            if ':' in voice_weight:
                voice, weight_str = voice_weight.strip().split(':')
                weight = float(weight_str) / 100.0  # Convert percentage to ratio
                blend[voice.strip()] = weight
                total_weight += weight
            else:
                blend[voice_weight.strip()] = 1.0
                total_weight += 1.0
        
        # Normalize weights
        if total_weight > 0:
            blend = {voice: weight/total_weight for voice, weight in blend.items()}
        
        return blend
    
    def _get_voice_lang(self, voice_id: str) -> str:
        """Get language code for voice."""
        if voice_id in self.VOICES:
            return self.VOICES[voice_id]["lang"]
        
        # Infer from voice ID prefix
        if voice_id.startswith('af_') or voice_id.startswith('am_'):
            return "en-us"
        elif voice_id.startswith('bf_') or voice_id.startswith('bm_'):
            return "en-uk"
        elif voice_id.startswith('ef_') or voice_id.startswith('em_'):
            return "es"
        elif voice_id.startswith('ff_') or voice_id.startswith('fm_'):
            return "fr"
        else:
            return "en-us"  # Default
    
    def _samples_to_wav_bytes(self, samples, sample_rate: int) -> bytes:
        """Convert audio samples to WAV bytes."""
        import io
        import wave
        import numpy as np
        
        # Ensure samples are in the right format for WAV
        if samples.dtype != np.int16:
            # Convert float to int16
            if samples.dtype == np.float32 or samples.dtype == np.float64:
                samples = (samples * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(samples.tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def get_available_languages(self) -> List[str]:
        """Get list of supported languages."""
        languages = set()
        for voice_info in self.VOICES.values():
            languages.add(voice_info["lang"])
        return sorted(list(languages))
    
    def get_voices_by_language(self, language: str) -> List[str]:
        """Get voices for a specific language."""
        voices = []
        for voice_id, voice_info in self.VOICES.items():
            if voice_info["lang"] == language:
                voices.append(voice_id)
        return voices
    
    def get_voices_by_gender(self, gender: str) -> List[str]:
        """Get voices by gender."""
        voices = []
        for voice_id, voice_info in self.VOICES.items():
            if voice_info["gender"].lower() == gender.lower():
                voices.append(voice_id)
        return voices