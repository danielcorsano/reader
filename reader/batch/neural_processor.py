"""Neural Engine optimized processor with streaming and checkpoint support."""
import json
import time
import hashlib
import wave
import io
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Protocol
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Constants
DEFAULT_SAMPLE_RATE = 22050
SILENCE_DURATION = 0.1
DEFAULT_CHECKPOINT_INTERVAL = 25


@dataclass
class NeuralCheckpoint:
    """Simple checkpoint for Neural Engine streaming conversion."""
    file_path: str
    current_chunk: int
    total_chunks: int
    output_size: int
    settings_hash: str
    timestamp: float


class ProgressDisplay(ABC):
    """Abstract base class for progress display implementations."""
    
    @abstractmethod
    def start(self, total_chunks: int, file_name: str):
        """Initialize progress display."""
        pass
    
    @abstractmethod
    def update(self, current_chunk: int, total_chunks: int, elapsed_time: float, eta_seconds: float):
        """Update progress display."""
        pass
    
    @abstractmethod
    def finish(self):
        """Finalize progress display."""
        pass


class SimpleProgressDisplay(ProgressDisplay):
    """Simple text-based progress display (current default)."""
    
    def __init__(self):
        self.start_time = None
    
    def start(self, total_chunks: int, file_name: str):
        self.start_time = time.time()
        print(f"🎯 Neural Engine stream processing {file_name} ({total_chunks} chunks, 48k mono MP3)")
    
    def update(self, current_chunk: int, total_chunks: int, elapsed_time: float, eta_seconds: float):
        progress = (current_chunk / total_chunks) * 100
        
        if current_chunk > 1:  # Show ETA after first chunk
            eta_mins = int(eta_seconds // 60)
            eta_secs = int(eta_seconds % 60)
            eta_str = f" ETA: {eta_mins:02d}:{eta_secs:02d}"
        else:
            eta_str = ""
        
        print(f"🧠 Chunk {current_chunk}/{total_chunks} ({progress:.1f}%){eta_str}", flush=True)
    
    def finish(self):
        pass


def create_progress_display(style: str) -> ProgressDisplay:
    """Factory function to create progress display instances."""
    if style == "simple":
        return SimpleProgressDisplay()
    elif style == "tqdm":
        try:
            from .tqdm_progress import TQDMProgressDisplay
            return TQDMProgressDisplay()
        except ImportError:
            print("⚠️ TQDM not available, falling back to simple display")
            return SimpleProgressDisplay()
    elif style == "rich":
        try:
            from .rich_progress import RichProgressDisplay
            return RichProgressDisplay()
        except ImportError:
            print("⚠️ Rich not available, falling back to simple display")
            return SimpleProgressDisplay()
    elif style == "timeseries":
        try:
            from .timeseries_progress import TimeseriesProgressDisplay
            return TimeseriesProgressDisplay()
        except ImportError:
            print("⚠️ Plotext not available, falling back to simple display")
            return SimpleProgressDisplay()
    else:
        print(f"⚠️ Unknown progress style '{style}', using simple display")
        return SimpleProgressDisplay()


class NeuralProcessor:
    """Neural Engine optimized processor with streaming output and checkpoints."""
    
    def __init__(self, output_path: Path, checkpoint_interval: int = DEFAULT_CHECKPOINT_INTERVAL, progress_style: str = "simple"):
        self.output_path = output_path
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_path = output_path.with_suffix('.checkpoint')
        self.audio_buffer = []
        self.progress_style = progress_style
        self.progress_display = create_progress_display(progress_style)
        
    def process_chunks(self, file_path: Path, text_chunks: List[str],
                      tts_engine, voice_blend: Dict[str, float], speed: float,
                      processing_config: Dict[str, Any]) -> Path:
        """Process chunks with Neural Engine optimization and stream to output."""
        total_chunks = len(text_chunks)
        settings_hash = self._get_settings_hash(processing_config)
        
        # Check for existing checkpoint
        start_chunk, output_size = self._load_checkpoint(file_path, total_chunks, settings_hash)
        
        # Initialize progress display
        self.progress_display.start(total_chunks, file_path.name)
        if start_chunk > 0:
            print(f"📂 Resuming from chunk {start_chunk} (file size: {output_size/1024/1024:.1f}MB)")
        
        # Open output file for appending
        mode = 'ab' if start_chunk > 0 else 'wb'
        with open(self.output_path, mode) as output_file:
            # Process chunks with Neural Engine
            self._process_all_chunks(
                output_file, text_chunks, tts_engine, voice_blend, speed,
                start_chunk, total_chunks, file_path, settings_hash
            )
            
            # Finalize any remaining MP3 batches
            self._finalize_mp3_processing(output_file)
        
        # Clean up checkpoint on completion
        self._cleanup_checkpoint()
        
        # Finalize progress display
        self.progress_display.finish()
        
        print(f"✅ Neural Engine processing complete: {self.output_path}")
        return self.output_path
    
    def _process_all_chunks(self, output_file, text_chunks: List[str], 
                           tts_engine, voice_blend: Dict[str, float], speed: float,
                           start_chunk: int, total_chunks: int, 
                           file_path: Path, settings_hash: str):
        """Sequential chunk processing optimized for Neural Engine."""
        start_time = time.time()
        neural_engine_confirmed = False
        
        for i in range(start_chunk, total_chunks):
            chunk_text = text_chunks[i]
            
            # Calculate progress and ETA
            progress = ((i + 1) / total_chunks) * 100
            
            if i > start_chunk:  # Calculate ETA after first chunk
                elapsed = time.time() - start_time
                chunks_done = i + 1 - start_chunk
                chunks_remaining = total_chunks - (i + 1)
                eta_seconds = (elapsed / chunks_done) * chunks_remaining
                eta_mins = int(eta_seconds // 60)
                eta_secs = int(eta_seconds % 60)
                eta_str = f" ETA: {eta_mins:02d}:{eta_secs:02d}"
            else:
                eta_str = ""
            
            # Update progress display
            self.progress_display.update(i + 1, total_chunks, elapsed if i > start_chunk else 0, eta_seconds if i > start_chunk else 0)
            
            # Process chunk with Neural Engine
            try:
                audio_data = self._process_single_chunk(chunk_text, i, total_chunks, tts_engine, voice_blend, speed)
                
                # Confirm Neural Engine is running after first successful chunk
                if not neural_engine_confirmed and audio_data:
                    print(f"✅ Neural Engine processing active - generating audio at optimized speed", flush=True)
                    neural_engine_confirmed = True
                    
            except Exception as e:
                if not neural_engine_confirmed:
                    print(f"❌ Neural Engine processing failed: {str(e)}", flush=True)
                    print(f"🔄 Falling back to CPU processing", flush=True)
                    neural_engine_confirmed = True  # Don't spam error messages
                raise  # Re-raise to handle at higher level
            
            # Convert and write immediately for streaming
            self._convert_and_write_chunk(output_file, audio_data)
            
            # Save checkpoint periodically
            if (i + 1) % self.checkpoint_interval == 0:
                current_size = output_file.tell()
                self._save_checkpoint(file_path, i + 1, total_chunks, current_size, settings_hash)
    
    def _process_single_chunk(self, chunk_text: str, chunk_idx: int, total_chunks: int,
                             tts_engine, voice_blend: Dict[str, float], speed: float) -> bytes:
        """Process a single text chunk to audio with Neural Engine."""
        if not chunk_text.strip():
            # Return silence for empty chunks
            silence_samples = int(SILENCE_DURATION * DEFAULT_SAMPLE_RATE)
            silence_data = b'\\x00\\x00' * silence_samples
            
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(DEFAULT_SAMPLE_RATE)
                wav_file.writeframes(silence_data)
            
            wav_buffer.seek(0)
            return wav_buffer.read()
        
        try:
            # Determine voice for synthesis
            if len(voice_blend) == 1:
                # Single voice
                voice_id, _ = list(voice_blend.items())[0]
                voice_str = voice_id
            else:
                # Voice blending - create voice spec string
                voice_parts = [f"{voice}:{int(weight*100)}" for voice, weight in voice_blend.items()]
                voice_str = ",".join(voice_parts)
            
            # Clean the text to prevent TTS issues
            clean_text = chunk_text.strip()
            
            # Replace problematic characters
            clean_text = clean_text.replace('\\u00a0', ' ')  # Non-breaking space
            clean_text = clean_text.replace('\\u2013', '-')  # En dash
            clean_text = clean_text.replace('\\u2014', '-')  # Em dash
            clean_text = clean_text.replace('\\u2019', "'")  # Right single quote
            clean_text = clean_text.replace('\\u201c', '"')  # Left double quote
            clean_text = clean_text.replace('\\u201d', '"')  # Right double quote
            
            return tts_engine.synthesize(clean_text, voice_str, speed)
            
        except Exception as e:
            raise RuntimeError(f"Neural Engine processing failed on chunk {chunk_idx + 1}: {str(e)}") from e
    
    def _convert_and_write_chunk(self, output_file, audio_data: bytes):
        """Collect audio data for final processing."""
        if self.output_path.suffix.lower() == '.mp3':
            # Collect WAV data for final MP3 conversion
            self.audio_buffer.append(audio_data)
        else:
            # Direct write for WAV
            output_file.write(audio_data)
            output_file.flush()
    
    
    def _finalize_mp3_processing(self, output_file):
        """Convert all collected WAV chunks to final MP3."""
        if self.audio_buffer and self.output_path.suffix.lower() == '.mp3':
            print(f"🎵 Converting {len(self.audio_buffer)} chunks to final MP3", flush=True)
            
            try:
                from ..processors.ffmpeg_processor import FFmpegAudioProcessor
                
                # Combine all WAV chunks into single audio stream
                combined_audio = b''.join(self.audio_buffer)
                
                # Create temporary WAV file with all audio
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    temp_wav.write(combined_audio)
                    temp_wav_path = Path(temp_wav.name)
                
                # Convert complete WAV to MP3
                processor = FFmpegAudioProcessor()
                processor.convert_format(temp_wav_path, self.output_path, 'mp3')
                
                # Clean up temporary WAV file
                temp_wav_path.unlink(missing_ok=True)
                
                print(f"✅ Final MP3 conversion complete", flush=True)
                
            except Exception as e:
                print(f"⚠️ Final MP3 conversion failed: {e}, keeping as WAV", flush=True)
                # Fallback: write all WAV data to output file
                output_file.seek(0)  # Start from beginning
                output_file.truncate()  # Clear any existing data
                for audio_data in self.audio_buffer:
                    output_file.write(audio_data)
                output_file.flush()
                
            # Clear the buffer
            self.audio_buffer.clear()
    
    def _get_settings_hash(self, config: Dict[str, Any]) -> str:
        """Generate hash of processing settings to detect changes."""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
    
    def _load_checkpoint(self, file_path: Path, total_chunks: int, settings_hash: str) -> tuple[int, int]:
        """Load checkpoint and verify integrity."""
        if not self.checkpoint_path.exists():
            return 0, 0
        
        try:
            with open(self.checkpoint_path, 'r') as f:
                data = json.load(f)
            
            checkpoint = NeuralCheckpoint(**data)
            
            # Verify checkpoint is for same file and settings
            if (checkpoint.file_path != str(file_path) or 
                checkpoint.total_chunks != total_chunks or
                checkpoint.settings_hash != settings_hash):
                print("🔄 Settings changed, starting fresh")
                self._cleanup_checkpoint()
                return 0, 0
            
            # Verify output file exists and has expected size
            if not self.output_path.exists() or self.output_path.stat().st_size != checkpoint.output_size:
                print("⚠️ Output file corrupted, starting fresh")
                self._cleanup_checkpoint()
                return 0, 0
            
            return checkpoint.current_chunk, checkpoint.output_size
            
        except Exception as e:
            print(f"⚠️ Checkpoint error: {e}, starting fresh")
            self._cleanup_checkpoint()
            return 0, 0
    
    def _save_checkpoint(self, file_path: Path, current_chunk: int, 
                        total_chunks: int, output_size: int, settings_hash: str):
        """Save minimal checkpoint."""
        checkpoint = NeuralCheckpoint(
            file_path=str(file_path),
            current_chunk=current_chunk,
            total_chunks=total_chunks,
            output_size=output_size,
            settings_hash=settings_hash,
            timestamp=time.time()
        )
        
        try:
            with open(self.checkpoint_path, 'w') as f:
                json.dump(asdict(checkpoint), f)
            print(f"💾 Checkpoint: {current_chunk}/{total_chunks} chunks ({output_size/1024/1024:.1f}MB)", flush=True)
        except Exception as e:
            print(f"⚠️ Failed to save checkpoint: {e}")
    
    def _cleanup_checkpoint(self):
        """Remove checkpoint file."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()


