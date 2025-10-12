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
    
    def __init__(self, debug: bool = False):
        """Initialize the Kokoro engine."""
        self.debug = debug
        if not KOKORO_AVAILABLE:
            raise ImportError("Kokoro ONNX not available. Install with: poetry add kokoro-onnx")
        
        self.kokoro = None
        self._initialized = False
        self._init_error = None
    
    # Kokoro voice mappings with language codes
    # Updated to match actual Kokoro library voice names
    VOICES = {
        # American English - using actual Kokoro voice names
        "af_sarah": {"name": "Sarah (American)", "lang": "en-us", "gender": "female"},
        "af_nicole": {"name": "Nicole (American)", "lang": "en-us", "gender": "female"},
        "am_michael": {"name": "Michael (American)", "lang": "en-us", "gender": "male"},
        "am_adam": {"name": "Adam (American)", "lang": "en-us", "gender": "male"},

        # British English
        "bf_emma": {"name": "Emma (British)", "lang": "en-uk", "gender": "female"},
        "bf_isabella": {"name": "Isabella (British)", "lang": "en-uk", "gender": "female"},
        "bm_oliver": {"name": "Oliver (British)", "lang": "en-uk", "gender": "male"},
        "bm_william": {"name": "William (British)", "lang": "en-uk", "gender": "male"},

        # Other languages (using consistent naming pattern)
        "ef_clara": {"name": "Clara (Spanish)", "lang": "es", "gender": "female"},
        "em_pedro": {"name": "Pedro (Spanish)", "lang": "es", "gender": "male"},
        "ff_marie": {"name": "Marie (French)", "lang": "fr", "gender": "female"},
        "fm_pierre": {"name": "Pierre (French)", "lang": "fr", "gender": "male"},
    }

    # Compiled regex patterns for text chunking (performance optimization)
    SENTENCE_SPLIT_PATTERN = re.compile(r'(?<=[.!?])\s+')
    PUNCTUATION_SPLIT_PATTERN = re.compile(r'([,;:—–\-])\s*')
    
    
    def _ensure_initialized(self) -> None:
        """Ensure Kokoro is initialized, initializing lazily if needed."""
        if self._initialized:
            if self.kokoro is None:
                raise RuntimeError(f"Kokoro initialization failed: {self._init_error}")
            return

        try:
            # Get model paths from cache directory
            from ..utils.model_downloader import get_cache_dir, download_models

            cache = get_cache_dir() / "kokoro"
            model_path = cache / "kokoro-v1.0.onnx"
            voices_path = cache / "voices-v1.0.bin"

            # Auto-download if not present
            if not model_path.exists() or not voices_path.exists():
                print("📥 Kokoro models not found. Downloading (~310MB)...")
                if not download_models(verbose=True):
                    raise FileNotFoundError(
                        f"Failed to download Kokoro models.\n"
                        f"💡 Try: reader download-models\n"
                        f"   Or check your internet connection"
                    )
            
            # Try to initialize with CoreML for Apple Neural Engine acceleration
            try:
                import platform
                if self.debug:
                    print(f"🔍 DEBUG: Platform: {platform.system()}, Machine: {platform.machine()}", flush=True)
                
                if platform.system() == "Darwin" and platform.machine() == "arm64":
                    # M1/M2/M3 Mac - try CoreML acceleration
                    import os
                    if self.debug:
                        print("🧠 Setting CoreML environment variables for Neural Engine...", flush=True)
                    os.environ["ORT_COREML_FLAGS"] = "COREML_FLAG_ENABLE_ON_SUBGRAPH"
                    if self.debug:
                        print(f"🔍 DEBUG: Set ORT_COREML_FLAGS={os.environ.get('ORT_COREML_FLAGS')}", flush=True)
                    print("🧠 Attempting Apple Neural Engine acceleration via CoreML...", flush=True)
                else:
                    print("⚠️ Not an Apple Silicon Mac - Neural Engine not available", flush=True)
                
                if self.debug:
                    print(f"🔍 DEBUG: Initializing Kokoro with model: {model_path}", flush=True)
                    print(f"🔍 DEBUG: Using voices: {voices_path}", flush=True)
                
                import time
                init_start = time.time()
                self.kokoro = Kokoro(str(model_path), str(voices_path))
                init_time = time.time() - init_start
                
                if self.debug:
                    print(f"🔍 DEBUG: Kokoro initialization took {init_time:.2f} seconds", flush=True)
                
                # Check if CoreML acceleration worked
                if platform.system() == "Darwin" and platform.machine() == "arm64":
                    print("✅ Kokoro initialized with Neural Engine acceleration (CoreML)", flush=True)
                    print(f"🚀 Optimized settings: 48k mono MP3, Neural Engine acceleration", flush=True)
                    
                    # Test inference speed
                    if self.debug:
                        print("🔍 DEBUG: Testing Neural Engine inference speed...", flush=True)
                        test_start = time.time()
                        test_audio = self.kokoro.create("Hello world", "am_michael")
                        test_time = time.time() - test_start
                        print(f"🔍 DEBUG: Test inference took {test_time:.3f} seconds for 'Hello world'", flush=True)
                        print(f"🔍 DEBUG: Generated {len(test_audio)} bytes of audio", flush=True)
                else:
                    print("✅ Kokoro initialized with CPU inference", flush=True)
                    
            except Exception as coreml_error:
                print(f"⚠️ CoreML acceleration failed, falling back to CPU: {coreml_error}", flush=True)
                # Clear CoreML environment variables and try regular initialization
                import os
                os.environ.pop("ORT_COREML_FLAGS", None)
                self.kokoro = Kokoro(str(model_path), str(voices_path))
                print("✅ Kokoro initialized with CPU fallback", flush=True)
            
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
            voice = "am_michael"

        # Validate voice exists (check primary voice in blend)
        primary_voice = voice.split(':')[0].split(',')[0].strip()
        if primary_voice not in self.VOICES:
            available_voices = ', '.join(sorted(self.VOICES.keys()))
            raise ValueError(
                f"Voice '{primary_voice}' not found. "
                f"Available voices: {available_voices}"
            )

        # Handle voice blending
        voice_blend = self._parse_voice_blend(voice)
        
        # Check text length and chunk if necessary (should rarely happen with optimized input)
        if len(text) > 450:  # Slightly higher limit since we pre-chunk at 400
            return self._synthesize_long_text(text, voice_blend, speed)
        
        try:
            # Generate audio with Kokoro for short text
            # Sanitize text to avoid index errors
            text = self._sanitize_text(text)

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

        except IndexError as e:
            # Handle index out of bounds errors in Kokoro
            if "out of bounds" in str(e):
                raise RuntimeError(f"Kokoro synthesis failed due to problematic text content: {e}")
            raise RuntimeError(f"Kokoro synthesis failed: {e}")
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

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to avoid Kokoro synthesis errors."""
        import re

        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if char.isprintable() or char in '\n\t ')

        # Replace problematic unicode characters
        replacements = {
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u2026': '...',  # Ellipsis
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        # Limit consecutive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Ensure text is not empty
        if not text.strip():
            text = "."

        return text.strip()

    def _synthesize_long_text(self, text: str, voice_blend: Dict[str, float], speed: float) -> bytes:
        """Synthesize long text by intelligent chunking with streaming to prevent memory issues."""
        # Split text into chunks at natural break points
        chunks = self._chunk_text_intelligently(text, max_length=400)
        
        if len(chunks) <= 4:
            # For smaller texts, use in-memory processing
            return self._synthesize_chunks_in_memory(chunks, voice_blend, speed)
        else:
            # For large texts, use streaming with temporary files
            return self._synthesize_chunks_streaming(chunks, voice_blend, speed)
    
    def _synthesize_chunks_in_memory(self, chunks: List[str], voice_blend: Dict[str, float], speed: float) -> bytes:
        """Memory-efficient synthesis for smaller chunk sets."""
        audio_segments = []
        sample_rate = None
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            try:
                # Sanitize chunk text
                sanitized_chunk = self._sanitize_text(chunk.strip())

                if len(voice_blend) == 1:
                    # Single voice
                    voice_id, _ = list(voice_blend.items())[0]
                    samples, chunk_sample_rate = self.kokoro.create(
                        text=sanitized_chunk,
                        voice=voice_id,
                        speed=speed,
                        lang=self._get_voice_lang(voice_id)
                    )
                else:
                    # Voice blending - use primary voice (highest weight)
                    primary_voice = max(voice_blend.items(), key=lambda x: x[1])[0]
                    samples, chunk_sample_rate = self.kokoro.create(
                        text=sanitized_chunk,
                        voice=primary_voice,
                        speed=speed,
                        lang=self._get_voice_lang(primary_voice)
                    )

                audio_segments.append(samples)
                if sample_rate is None:
                    sample_rate = chunk_sample_rate

            except Exception as e:
                # Log the error but continue with other chunks
                print(f"⚠️  Warning: Skipping chunk {i+1} due to synthesis error: {e}")
                print(f"    Chunk preview: {chunk[:80]}...")
                continue
        
        if not audio_segments:
            raise RuntimeError("Failed to synthesize any chunks from the text")
        
        # Merge audio segments
        import numpy as np
        merged_samples = np.concatenate(audio_segments)
        
        # Convert to WAV bytes
        return self._samples_to_wav_bytes(merged_samples, sample_rate)
    
    def _synthesize_chunks_streaming(self, chunks: List[str], voice_blend: Dict[str, float], speed: float) -> bytes:
        """Memory-efficient synthesis using temporary files for large texts."""
        import tempfile
        
        temp_files = []
        sample_rate = None
        total_chunks = len(chunks)
        
        try:
            # Process chunks and save to temporary files
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                try:
                    # Sanitize chunk text
                    sanitized_chunk = self._sanitize_text(chunk.strip())

                    if len(voice_blend) == 1:
                        # Single voice
                        voice_id, _ = list(voice_blend.items())[0]
                        samples, chunk_sample_rate = self.kokoro.create(
                            text=sanitized_chunk,
                            voice=voice_id,
                            speed=speed,
                            lang=self._get_voice_lang(voice_id)
                        )
                    else:
                        # Voice blending - use primary voice (highest weight)
                        primary_voice = max(voice_blend.items(), key=lambda x: x[1])[0]
                        samples, chunk_sample_rate = self.kokoro.create(
                            text=sanitized_chunk,
                            voice=primary_voice,
                            speed=speed,
                            lang=self._get_voice_lang(primary_voice)
                        )

                    if sample_rate is None:
                        sample_rate = chunk_sample_rate

                    # Save to temporary file
                    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                    wav_data = self._samples_to_wav_bytes(samples, chunk_sample_rate)
                    temp_file.write(wav_data)
                    temp_file.close()
                    temp_files.append(temp_file.name)

                except Exception as e:
                    # Log the error but continue with other chunks
                    print(f"⚠️  Warning: Skipping chunk {i+1} due to synthesis error: {e}")
                    print(f"    Chunk preview: {chunk[:80]}...")
                    continue
            
            if not temp_files:
                raise RuntimeError("Failed to synthesize any chunks from the text")
            
            # Concatenate temporary files
            print(f"Merging {len(temp_files)} audio segments...")
            return self._concatenate_temp_files(temp_files, sample_rate)
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    Path(temp_file).unlink(missing_ok=True)
                except:
                    pass
    
    def _concatenate_temp_files(self, temp_files: List[str], sample_rate: int) -> bytes:
        """Concatenate temporary audio files into a single audio stream."""
        import wave
        import io
        
        # Read all WAV files and concatenate the audio data
        all_audio_data = []
        
        for temp_file in temp_files:
            try:
                with wave.open(temp_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
                    all_audio_data.append(audio_data)
            except Exception as e:
                print(f"Warning: Failed to read temp file {temp_file}: {e}")
                continue
        
        if not all_audio_data:
            raise RuntimeError("Failed to read any temporary audio files")
        
        # Create final WAV file in memory
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Write all concatenated audio data
            for audio_data in all_audio_data:
                wav_file.writeframes(audio_data)
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def _chunk_text_intelligently(self, text: str, max_length: int = 400) -> List[str]:
        """Chunk text at natural break points while staying under max_length."""
        chunks = []
        current_chunk = ""

        # Split by sentences first (using pre-compiled pattern)
        sentences = self.SENTENCE_SPLIT_PATTERN.split(text)

        for sentence in sentences:
            # If sentence itself is too long, split by smaller units
            if len(sentence) > max_length:
                # Split by commas, semicolons, or other punctuation (using pre-compiled pattern)
                sub_parts = self.PUNCTUATION_SPLIT_PATTERN.split(sentence)
                temp_part = ""
                
                for i, part in enumerate(sub_parts):
                    if len(temp_part + part) <= max_length:
                        temp_part += part
                    else:
                        if temp_part.strip():
                            chunks.append(temp_part.strip())
                        temp_part = part
                
                if temp_part.strip():
                    if len(current_chunk + " " + temp_part) <= max_length:
                        current_chunk += " " + temp_part if current_chunk else temp_part
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = temp_part
            else:
                # Check if we can add this sentence to current chunk
                if len(current_chunk + " " + sentence) <= max_length:
                    current_chunk += " " + sentence if current_chunk else sentence
                else:
                    # Current chunk is full, start new one
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

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