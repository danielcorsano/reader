"""Neural Engine optimized processor with streaming and checkpoint support."""
import gc
import json
import time
import hashlib
import wave
import io
import struct
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Text processing utilities
from ..text_processing.number_expander import get_number_expander

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


def create_progress_display(style: str, debug: bool = False) -> ProgressDisplay:
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
            return TimeseriesProgressDisplay(debug=debug)
        except ImportError:
            print("⚠️ Plotext not available, falling back to simple display")
            return SimpleProgressDisplay()
    else:
        print(f"⚠️ Unknown progress style '{style}', using simple display")
        return SimpleProgressDisplay()


class NeuralProcessor:
    """Neural Engine optimized processor with streaming output and checkpoints."""

    def __init__(self, output_path: Path, checkpoint_interval: int = DEFAULT_CHECKPOINT_INTERVAL,
                 progress_style: str = "timeseries", character_mapper=None, dialogue_detector=None, debug: bool = False,
                 final_output_dir: Path = None):
        self.output_path = output_path
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_path = output_path.with_suffix('.checkpoint')
        self.progress_style = progress_style
        self.debug = debug
        self.progress_display = create_progress_display(progress_style, debug=debug)
        self.final_output_dir = final_output_dir or (Path.home() / "Downloads")

        # Debug logging
        self.debug_log = Path.home() / ".cache/audiobook-reader/debug.log" if debug else None
        if self.debug:
            self.debug_log.parent.mkdir(parents=True, exist_ok=True)
            self.debug_log.unlink(missing_ok=True)
            with open(self.debug_log, 'w') as f:
                import os
                f.write(f"=== NeuralProcessor.__init__ at {time.time()} (PID {os.getpid()}) ===\n")
                f.write(f"Progress display: {type(self.progress_display).__name__}\n")

        # Character voice support
        self.character_mapper = character_mapper
        self.dialogue_detector = dialogue_detector

        # For MP3 output, use intermediate WAV file for streaming
        self.is_mp3_output = output_path.suffix.lower() == '.mp3'
        self.temp_wav_path = output_path.with_suffix('.wav.tmp') if self.is_mp3_output else None

        # Time-based checkpointing (track last checkpoint time)
        self.last_checkpoint_time = 0
        self.checkpoint_interval_seconds = 60  # Save checkpoint every 60 seconds

        # Number expansion for TTS (singleton instance)
        self.number_expander = get_number_expander()
        
    def process_chunks(self, file_path: Path, text_chunks: List[str],
                      tts_engine, voice_blend: Dict[str, float], speed: float,
                      processing_config: Dict[str, Any]) -> Path:
        """Process chunks with Neural Engine optimization and stream to output."""
        total_chunks = len(text_chunks)
        settings_hash = self._get_settings_hash(processing_config)

        # Check for lock file (another process working on this file)
        lock_path = self.output_path.with_suffix('.lock')
        if lock_path.exists():
            print(f"⚠️ Another process is already converting this file.")
            print(f"   If this is incorrect, delete: {lock_path}")
            raise RuntimeError(f"Conversion already in progress for {file_path.name}")

        # Create lock file
        try:
            with open(lock_path, 'w') as f:
                import os
                f.write(f"{os.getpid()}\n")
        except Exception as e:
            print(f"⚠️ Could not create lock file: {e}")

        try:
            # Check for existing checkpoint
            start_chunk, output_size = self._load_checkpoint(file_path, total_chunks, settings_hash)

            # Initialize progress display
            self.progress_display.start(total_chunks, file_path.name)
            if start_chunk > 0:
                print(f"📂 Resuming from chunk {start_chunk} (file size: {output_size/1024/1024:.1f}MB)")

            # For MP3: stream to temp WAV, for WAV: stream directly
            actual_output_path = self.temp_wav_path if self.is_mp3_output else self.output_path
            mode = 'ab' if start_chunk > 0 else 'wb'

            with open(actual_output_path, mode) as output_file:
                # Process chunks with Neural Engine
                self._process_all_chunks(
                    output_file, text_chunks, tts_engine, voice_blend, speed,
                    start_chunk, total_chunks, file_path, settings_hash
                )

                # Convert temp WAV to MP3 if needed
                if self.is_mp3_output:
                    self._convert_wav_to_mp3()

                # Clean up checkpoint on completion
                self._cleanup_checkpoint()

                # Finalize progress display
                self.progress_display.finish()

                # Move finished file to finished folder
                finished_path = self._move_to_finished()

                print(f"✅ Neural Engine processing complete: {finished_path}")
                return finished_path
        finally:
            # Always remove lock file, even on error
            if lock_path.exists():
                lock_path.unlink()
    
    def _process_all_chunks(self, output_file, text_chunks: List[str],
                           tts_engine, voice_blend: Dict[str, float], speed: float,
                           start_chunk: int, total_chunks: int,
                           file_path: Path, settings_hash: str):
        """Sequential chunk processing optimized for Neural Engine."""
        start_time = time.time()
        neural_engine_confirmed = False

        if self.debug:
            with open(self.debug_log, 'a') as f:
                f.write(f"\n=== _process_all_chunks ===\n")
                f.write(f"start_chunk={start_chunk}, total_chunks={total_chunks}\n")

        skipped_chunks = []
        for i in range(start_chunk, total_chunks):
            chunk_text = text_chunks[i]
            
            # Calculate progress and ETA for progress display
            if i > start_chunk:  # Calculate ETA after first chunk
                elapsed = time.time() - start_time
                chunks_done = i + 1 - start_chunk
                chunks_remaining = total_chunks - (i + 1)
                eta_seconds = (elapsed / chunks_done) * chunks_remaining
            else:
                elapsed = 0
                eta_seconds = 0
            
            # Update progress display
            self.progress_display.update(i + 1, total_chunks, elapsed, eta_seconds)
            
            # Process chunk with Neural Engine
            try:
                audio_data = self._process_single_chunk(chunk_text, i, total_chunks, tts_engine, voice_blend, speed)
                
                # Confirm Neural Engine is running after first successful chunk
                # (suppress for screen-clearing displays to avoid visual clutter)
                if not neural_engine_confirmed and audio_data:
                    if self.progress_style == "simple":
                        print(f"✅ Neural Engine processing active - generating audio at optimized speed", flush=True)
                    neural_engine_confirmed = True

            except Exception as e:
                error_str = str(e)

                # Check if this is the Kokoro phoneme limit bug (510 phonemes)
                if "510" in error_str and "out of bounds" in error_str:
                    print(f"\n⚠️  Chunk {i+1} exceeds phoneme limit - splitting into smaller pieces", flush=True)

                    # Split chunk into smaller pieces and process each
                    # Find sentence boundaries for clean splits
                    sentences = []
                    current = []
                    for char in chunk_text:
                        current.append(char)
                        if char in '.!?':
                            sentences.append(''.join(current).strip())
                            current = []
                    if current:
                        sentences.append(''.join(current).strip())

                    # Process each sentence separately
                    audio_parts = []
                    for j, sentence in enumerate(sentences):
                        if not sentence.strip():
                            continue
                        try:
                            audio_part = self._process_single_chunk(sentence, i, total_chunks, tts_engine, voice_blend, speed)
                            # Strip WAV header from all but first part
                            if j > 0 and len(audio_part) > 44:
                                audio_part = audio_part[44:]
                            audio_parts.append(audio_part)
                        except Exception as sent_error:
                            # If even a single sentence fails, split it in half
                            half = len(sentence) // 2
                            try:
                                part1 = self._process_single_chunk(sentence[:half], i, total_chunks, tts_engine, voice_blend, speed)
                                part2 = self._process_single_chunk(sentence[half:], i, total_chunks, tts_engine, voice_blend, speed)
                                audio_parts.append(part1)
                                if len(part2) > 44:
                                    audio_parts.append(part2[44:])
                            except Exception as final_error:
                                print(f"⚠️  Cannot synthesize part of chunk {i+1}, skipping this segment", flush=True)
                                continue

                    if not audio_parts:
                        skipped_chunks.append(i + 1)
                        print(f"\n⚠️  Warning: Skipping chunk {i+1} entirely - no segments could be synthesized", flush=True)
                        continue

                    audio_data = b''.join(audio_parts)
                    print(f"✅ Successfully processed chunk {i+1} in {len(sentences)} pieces", flush=True)
                else:
                    # Other errors - log and re-raise
                    if self.debug:
                        with open(self.debug_log, 'a') as f:
                            import traceback
                            f.write(f"\n!!! EXCEPTION chunk {i+1} !!!\n")
                            f.write(f"{e}\nLength: {len(chunk_text)}\n")
                            f.write(traceback.format_exc())

                    if not neural_engine_confirmed:
                        if self.progress_style == "simple":
                            print(f"❌ Neural Engine processing failed: {str(e)}", flush=True)
                            print(f"🔄 Falling back to CPU processing", flush=True)
                        neural_engine_confirmed = True  # Don't spam error messages
                    raise  # Re-raise to handle at higher level
            
            # Convert and write immediately for streaming
            self._convert_and_write_chunk(output_file, audio_data)

            # Save checkpoint periodically (time-based with chunk-based fallback)
            current_time = time.time()
            time_since_last_checkpoint = current_time - self.last_checkpoint_time

            # Checkpoint if either: 60 seconds passed OR chunk interval reached
            should_checkpoint = (
                time_since_last_checkpoint >= self.checkpoint_interval_seconds or
                (i + 1) % self.checkpoint_interval == 0
            )

            if should_checkpoint:
                current_size = output_file.tell()  # Actual file size (WAV or temp WAV)
                self._save_checkpoint(file_path, i + 1, total_chunks, current_size, settings_hash)
                self.last_checkpoint_time = current_time
                gc.collect()  # Release accumulated TTS memory

        # Report skipped chunks summary
        if skipped_chunks:
            print(f"\n⚠️  Completed with {len(skipped_chunks)} skipped chunk(s): {', '.join(map(str, skipped_chunks))}")
    
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
            # Clean the text to prevent TTS issues
            clean_text = chunk_text.strip()

            # Expand numbers to words BEFORE character replacement (for better pronunciation)
            clean_text = self.number_expander.expand_numbers(clean_text)

            # Replace problematic characters
            clean_text = clean_text.replace('\\u00a0', ' ')  # Non-breaking space
            clean_text = clean_text.replace('\\u2013', '-')  # En dash
            clean_text = clean_text.replace('\\u2014', '-')  # Em dash
            clean_text = clean_text.replace('\\u2019', "'")  # Right single quote
            clean_text = clean_text.replace('\\u201c', '"')  # Left double quote
            clean_text = clean_text.replace('\\u201d', '"')  # Right double quote

            # Character voice detection - detect speaker and use appropriate voice
            if self.character_mapper and self.dialogue_detector:
                # Analyze chunk for dialogue
                segments = self.dialogue_detector.analyze_text(clean_text)

                # If we have dialogue segments with speakers, process them separately
                if any(seg.is_dialogue and seg.speaker for seg in segments):
                    return self._synthesize_with_character_voices(segments, tts_engine, voice_blend, speed)

            # Default: use provided voice blend (narrator voice)
            if len(voice_blend) == 1:
                # Single voice
                voice_id, _ = list(voice_blend.items())[0]
                voice_str = voice_id
            else:
                # Voice blending - create voice spec string
                voice_parts = [f"{voice}:{int(weight*100)}" for voice, weight in voice_blend.items()]
                voice_str = ",".join(voice_parts)

            return tts_engine.synthesize(clean_text, voice_str, speed)

        except Exception as e:
            raise RuntimeError(f"Neural Engine processing failed on chunk {chunk_idx + 1}: {str(e)}") from e

    def _synthesize_with_character_voices(self, segments: List, tts_engine,
                                         default_voice_blend: Dict[str, float], speed: float) -> bytes:
        """Synthesize text segments with character-specific voices."""
        audio_parts = []

        for segment in segments:
            if not segment.text.strip():
                continue

            # Determine voice for this segment
            if segment.is_dialogue and segment.speaker:
                # Get character voice mapping
                char_voice = self.character_mapper.get_character_voice(segment.speaker)
                if char_voice:
                    voice_str = char_voice.voice_id
                else:
                    # Speaker detected but no mapping - use default voice
                    voice_str = self._voice_blend_to_str(default_voice_blend)
            else:
                # Narration - use default narrator voice
                voice_str = self._voice_blend_to_str(default_voice_blend)

            # Synthesize segment
            try:
                audio_data = tts_engine.synthesize(segment.text.strip(), voice_str, speed)
                audio_parts.append(audio_data)
            except Exception as e:
                # Fall back to default voice on error
                voice_str = self._voice_blend_to_str(default_voice_blend)
                audio_data = tts_engine.synthesize(segment.text.strip(), voice_str, speed)
                audio_parts.append(audio_data)

        # Concatenate all audio parts
        if not audio_parts:
            # Return silence if nothing was synthesized
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

        return self._concatenate_audio_segments(audio_parts)

    def _voice_blend_to_str(self, voice_blend: Dict[str, float]) -> str:
        """Convert voice blend dict to voice string."""
        if len(voice_blend) == 1:
            voice_id, _ = list(voice_blend.items())[0]
            return voice_id
        else:
            voice_parts = [f"{voice}:{int(weight*100)}" for voice, weight in voice_blend.items()]
            return ",".join(voice_parts)

    def _concatenate_audio_segments(self, audio_parts: List[bytes]) -> bytes:
        """Concatenate multiple WAV audio segments into one."""
        all_audio_data = []
        sample_rate = DEFAULT_SAMPLE_RATE

        for audio_data in audio_parts:
            try:
                wav_buffer = io.BytesIO(audio_data)
                with wave.open(wav_buffer, 'rb') as wav_file:
                    sample_rate = wav_file.getframerate()
                    frames = wav_file.readframes(wav_file.getnframes())

                    # Trim to zero crossing in last ~10ms to prevent clicks
                    search_len = min(440, len(frames))  # 220 samples * 2 bytes
                    if search_len >= 4:
                        samples = struct.unpack(f'<{search_len//2}h', frames[-search_len:])
                        for i in range(len(samples)-1, 0, -1):
                            if samples[i] * samples[i-1] <= 0:  # Zero crossing
                                frames = frames[:len(frames)-(len(samples)-i)*2]
                                break

                    all_audio_data.append(frames)
            except Exception as e:
                # Skip corrupted segments
                continue

        if not all_audio_data:
            raise RuntimeError("Failed to concatenate audio segments")

        # Create final WAV
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            for audio_data in all_audio_data:
                wav_file.writeframes(audio_data)

        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def _convert_and_write_chunk(self, output_file, audio_data: bytes):
        """Stream WAV chunk data directly to disk."""
        # Extract audio data from WAV chunk (skip header) and write to file
        wav_buffer = io.BytesIO(audio_data)
        with wave.open(wav_buffer, 'rb') as wav:
            audio_frames = wav.readframes(wav.getnframes())
            output_file.write(audio_frames)
            output_file.flush()
    

    def _convert_wav_to_mp3(self):
        """Convert streamed raw PCM temp file to final MP3 using FFmpeg directly.

        Reads raw PCM from disk without loading into memory - FFmpeg handles
        the streaming conversion to prevent out-of-memory on large books.
        """
        if not self.temp_wav_path or not self.temp_wav_path.exists():
            return

        file_size_mb = self.temp_wav_path.stat().st_size / (1024 * 1024)
        print(f"🎵 Converting {file_size_mb:.0f}MB raw audio to MP3 (streaming via FFmpeg)", flush=True)

        try:
            import subprocess
            from ..utils.setup import get_ffmpeg_path
            from ..config import ConfigManager

            bitrate = ConfigManager().config.audio.bitrate

            # Feed raw PCM directly to FFmpeg - no need to reconstruct WAV in memory
            cmd = [
                get_ffmpeg_path(),
                '-f', 's16le',                    # Raw signed 16-bit little-endian PCM
                '-ar', str(DEFAULT_SAMPLE_RATE),   # Sample rate (22050)
                '-ac', '1',                        # Mono
                '-i', str(self.temp_wav_path),     # Read raw PCM from disk
                '-c:a', 'libmp3lame',
                '-b:a', bitrate,
                '-q:a', '6',
                '-ac', '1',
                '-y', str(self.output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, check=True)

            # Clean up temp raw PCM file
            self.temp_wav_path.unlink(missing_ok=True)

            print(f"✅ MP3 conversion complete", flush=True)

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else str(e)
            print(f"⚠️ MP3 conversion failed: {stderr}", flush=True)
            # Fallback: add WAV header and keep as WAV
            self._fallback_save_as_wav()
        except Exception as e:
            print(f"⚠️ MP3 conversion failed: {e}, keeping as WAV", flush=True)
            self._fallback_save_as_wav()

    def _fallback_save_as_wav(self):
        """Save raw PCM temp file as proper WAV when MP3 conversion fails.

        Streams in chunks to avoid loading entire file into memory.
        """
        if not self.temp_wav_path or not self.temp_wav_path.exists():
            return
        wav_output = self.output_path.with_suffix('.wav')
        raw_size = self.temp_wav_path.stat().st_size
        try:
            with wave.open(str(wav_output), 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(DEFAULT_SAMPLE_RATE)
                # Stream raw PCM data in 8MB chunks
                with open(self.temp_wav_path, 'rb') as raw_f:
                    while True:
                        chunk = raw_f.read(8 * 1024 * 1024)
                        if not chunk:
                            break
                        wav_file.writeframes(chunk)
            self.temp_wav_path.unlink(missing_ok=True)
            # Update output_path so _move_to_finished finds the right file
            self.output_path = wav_output
        except Exception as fallback_err:
            print(f"⚠️ WAV fallback also failed: {fallback_err}", flush=True)
    
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

            # Normalize file_path to relative for comparison with checkpoint
            try:
                relative_path = str(Path(file_path).relative_to(Path.cwd()))
            except ValueError:
                # If file is outside cwd, use absolute path
                relative_path = str(file_path)

            # Debug: checkpoint verification
            if self.debug:
                with open(self.debug_log, 'a') as f:
                    f.write(f"\n=== Checkpoint verification ===\n")
                    f.write(f"File match: {checkpoint.file_path == relative_path}\n")
                    f.write(f"Chunks match: {checkpoint.total_chunks == total_chunks}\n")
                    f.write(f"Settings match: {checkpoint.settings_hash == settings_hash}\n")

            # Verify checkpoint is for same file and settings
            if (checkpoint.file_path != relative_path or
                checkpoint.total_chunks != total_chunks or
                checkpoint.settings_hash != settings_hash):
                print("🔄 Settings changed, starting fresh")
                self._cleanup_checkpoint()
                return 0, 0

            # For MP3: check temp WAV file, for WAV: check output file
            actual_file = self.temp_wav_path if self.is_mp3_output else self.output_path

            # Verify file exists
            if not actual_file.exists():
                print("⚠️ Output file missing, starting fresh")
                self._cleanup_checkpoint()
                return 0, 0

            # Check file integrity
            file_size = actual_file.stat().st_size

            if file_size < checkpoint.output_size:
                print(f"⚠️ File corrupted (truncated), starting fresh")
                self._cleanup_checkpoint()
                return 0, 0
            elif file_size > checkpoint.output_size:
                # Truncate extra data written after last checkpoint
                print(f"📐 Truncating {file_size - checkpoint.output_size} bytes of partial data")
                with open(actual_file, 'r+b') as f:
                    f.truncate(checkpoint.output_size)

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
            
            # Suppress checkpoint messages for screen-clearing displays to avoid visual clutter
            # (timeseries/rich displays clear screen and show their own progress)
        except Exception as e:
            print(f"⚠️ Failed to save checkpoint: {e}")
    
    def _cleanup_checkpoint(self):
        """Remove checkpoint and temp files."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
        # Clean up temp WAV if it still exists
        if self.temp_wav_path and self.temp_wav_path.exists():
            self.temp_wav_path.unlink()

    def _move_to_finished(self) -> Path:
        """Move completed file to final output directory."""
        import shutil

        # Ensure output directory exists
        self.final_output_dir.mkdir(parents=True, exist_ok=True)

        # Create destination path
        final_path = self.final_output_dir / self.output_path.name

        # Move the file if it exists
        if self.output_path.exists():
            shutil.move(str(self.output_path), str(final_path))
            return final_path
        else:
            return self.output_path  # Return original if file doesn't exist


