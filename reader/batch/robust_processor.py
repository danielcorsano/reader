"""Robust batch processor with checkpoint recovery and error handling."""
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
import traceback
import psutil

from .checkpoint_manager import CheckpointManager, ProcessingCheckpoint
from ..interfaces.text_parser import ParsedContent


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    checkpoint_interval: int = 50  # Save checkpoint every N chunks
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    continue_on_error: bool = True
    cleanup_on_completion: bool = True
    max_checkpoint_age_hours: int = 24
    # Rolling checkpoint settings - minimal for recovery only
    max_checkpoint_segments: int = 50   # Keep only last 50 segments in checkpoint for recovery
    keep_checkpoint_history: int = 2    # Keep only last 2 checkpoint intervals
    # Resource management - Optimized for Neural Engine acceleration
    thermal_management: bool = True  # Enable thermal throttling
    chunk_delay_seconds: float = 0.1  # Minimal delay for Neural Engine efficiency
    cool_down_interval: int = 20  # Cool down every 20 chunks (less frequent)
    cool_down_seconds: float = 2.0  # Shorter cool down duration
    max_cpu_usage_percent: float = 85.0  # Higher threshold for Neural Engine
    cpu_check_interval: int = 10  # Check CPU usage less frequently


class RobustProcessor:
    """Robust processor with automatic checkpointing and error recovery."""
    
    def __init__(self, batch_config: Optional[BatchConfig] = None,
                 checkpoint_dir: Optional[Path] = None):
        """Initialize robust processor."""
        self.config = batch_config or BatchConfig()
        self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        
        # Cleanup old checkpoints on startup
        self.checkpoint_manager.cleanup_old_checkpoints(
            self.config.max_checkpoint_age_hours
        )
    
    def process_with_checkpoints(self, 
                               file_path: Path,
                               parsed_content: ParsedContent,
                               processing_config: Dict[str, Any],
                               chunk_processor: Callable[[str, int, int], bytes],
                               text_chunks: List[str]) -> List[bytes]:
        """
        Process text chunks with automatic checkpointing and recovery.
        
        Args:
            file_path: Source file being processed
            parsed_content: Parsed content metadata
            processing_config: Processing configuration for checkpointing
            chunk_processor: Function that processes a single chunk (text, chunk_idx, total) -> audio_bytes
            text_chunks: List of text chunks to process
            
        Returns:
            List of audio segments as bytes
        """
        total_chunks = len(text_chunks)
        
        print(f"\n🎯 Processing {file_path.name} ({total_chunks} chunks)")
        
        # Try to load existing checkpoint
        checkpoint = self.checkpoint_manager.load_checkpoint(file_path)
        
        if checkpoint:
            # Resume from checkpoint - but we need to rebuild the COMPLETE file
            print(f"📂 Found checkpoint at {checkpoint.chunks_completed}/{checkpoint.total_chunks}")
            if checkpoint.chunks_completed >= checkpoint.total_chunks:
                # Already completed - clear checkpoint and start fresh for new settings
                print(f"🔄 Checkpoint shows completion, clearing for fresh conversion")
                self.checkpoint_manager.clear_checkpoint(file_path)
                audio_segments = []
                start_chunk = 0
            else:
                # Resume from where we left off - reconstruct ALL segments processed so far
                print(f"📂 Resuming from chunk {checkpoint.chunks_completed}")
                print(f"🔄 Reconstructing {checkpoint.chunks_completed} processed segments...")
                audio_segments = self._reconstruct_all_segments(file_path, checkpoint.chunks_completed)
                start_chunk = checkpoint.chunks_completed
        else:
            # Start fresh
            print(f"🆕 Starting fresh processing")
            audio_segments = []
            start_chunk = 0
        
        # Process remaining chunks
        for i in range(start_chunk, total_chunks):
            chunk_text = text_chunks[i]
            retry_count = 0
            
            while retry_count <= self.config.max_retries:
                try:
                    # Calculate accurate progress and ETA
                    progress_percent = ((i+1)/total_chunks)*100
                    eta_chunks = total_chunks - (i+1)
                    
                    # Dynamic ETA calculation based on actual processing time
                    if hasattr(self, '_chunk_times') and self._chunk_times:
                        avg_chunk_time = sum(self._chunk_times) / len(self._chunk_times)
                        estimated_seconds = eta_chunks * avg_chunk_time
                        estimated_minutes = estimated_seconds / 60
                    else:
                        # Fallback conservative estimate
                        estimated_minutes = (eta_chunks * (self.config.chunk_delay_seconds + 3)) / 60
                    
                    # Get current CPU usage and memory info
                    cpu_usage = psutil.cpu_percent(interval=0.1)
                    memory_info = psutil.virtual_memory()
                    memory_gb = memory_info.used / (1024**3)
                    
                    # Calculate total audio size so far
                    if hasattr(self, '_total_audio_size'):
                        total_size_mb = self._total_audio_size / (1024 * 1024)
                    else:
                        total_size_mb = 0
                    
                    print(f"🔄 Processing chunk {i+1}/{total_chunks} ({progress_percent:.1f}%)", flush=True)
                    print(f"   📊 ETA: ~{estimated_minutes:.0f}min | Audio: {total_size_mb:.1f}MB | Memory: {memory_gb:.1f}GB", flush=True)
                    print(f"   💻 CPU: {cpu_usage:.1f}% | Chunk: {eta_chunks} remaining", flush=True)
                    
                    # Show chunk text preview (first 50 chars)
                    preview = chunk_text.strip()[:50]
                    if len(chunk_text.strip()) > 50:
                        preview += "..."
                    print(f"   📝 Text: {preview}", flush=True)
                    
                    # Process the chunk
                    chunk_start_time = time.time()
                    audio_data = chunk_processor(chunk_text, i, total_chunks)
                    chunk_duration = time.time() - chunk_start_time
                    
                    # Track timing for accurate ETA
                    if not hasattr(self, '_chunk_times'):
                        self._chunk_times = []
                        self._total_audio_size = 0
                    
                    self._chunk_times.append(chunk_duration + self.config.chunk_delay_seconds)
                    # Keep only last 10 measurements for rolling average
                    if len(self._chunk_times) > 10:
                        self._chunk_times.pop(0)
                    
                    audio_segments.append(audio_data)
                    
                    # Update total audio size tracking
                    chunk_size_mb = len(audio_data) / (1024 * 1024)
                    self._total_audio_size += len(audio_data)
                    
                    # Show processing stats
                    print(f"   ⏱️ Processed in {chunk_duration:.1f}s, +{chunk_size_mb:.1f}MB audio", flush=True)
                    
                    # Thermal management - add delays to prevent overheating
                    if self.config.thermal_management:
                        # Check CPU usage and add extra delay if needed
                        if cpu_usage > self.config.max_cpu_usage_percent:
                            extra_delay = min(10.0, (cpu_usage - self.config.max_cpu_usage_percent) * 0.2)
                            print(f"🚨 High CPU usage ({cpu_usage:.1f}%) - adding {extra_delay:.1f}s extra delay", flush=True)
                            time.sleep(extra_delay)
                        
                        # Small delay between chunks
                        if self.config.chunk_delay_seconds > 0:
                            print(f"⏸️ Waiting {self.config.chunk_delay_seconds}s to prevent overheating...", flush=True)
                            time.sleep(self.config.chunk_delay_seconds)
                        
                        # Longer cool-down every N chunks
                        if (i + 1) % self.config.cool_down_interval == 0:
                            print(f"🌡️ System cool-down: {self.config.cool_down_seconds}s pause...", flush=True)
                            time.sleep(self.config.cool_down_seconds)
                            print(f"❄️ Cool-down complete, resuming processing...", flush=True)
                    
                    # Save checkpoint periodically with rolling strategy
                    if (i + 1) % self.config.checkpoint_interval == 0:
                        # Use rolling checkpoint - keep only recent segments
                        checkpoint_segments = audio_segments[-self.config.max_checkpoint_segments:]
                        checkpoint_start = max(0, (i + 1) - len(checkpoint_segments))
                        
                        self._save_checkpoint(
                            file_path, i + 1, total_chunks, 
                            checkpoint_segments, processing_config
                        )
                        
                        print(f"📊 Rolling checkpoint: keeping {len(checkpoint_segments)} recent segments")
                        
                        # Clean up old segment files to save space
                        self._cleanup_old_segment_files(file_path, checkpoint_start)
                    
                    break  # Success, move to next chunk
                    
                except Exception as e:
                    retry_count += 1
                    error_msg = str(e)
                    
                    print(f"❌ Error processing chunk {i+1}: {error_msg}")
                    
                    if retry_count <= self.config.max_retries:
                        print(f"🔄 Retrying chunk {i+1} (attempt {retry_count}/{self.config.max_retries})")
                        time.sleep(self.config.retry_delay_seconds)
                    else:
                        # Max retries exceeded
                        if self.config.continue_on_error:
                            print(f"⚠️ Skipping chunk {i+1} after {self.config.max_retries} failed attempts")
                            print(f"🔄 Continuing with next chunk...")
                            
                            # Save checkpoint with current progress
                            self._save_checkpoint(
                                file_path, i + 1, total_chunks,
                                audio_segments, processing_config
                            )
                            break
                        else:
                            # Save checkpoint before failing
                            self._save_checkpoint(
                                file_path, i, total_chunks,
                                audio_segments, processing_config
                            )
                            
                            print(f"💥 Processing failed on chunk {i+1}.")
                            print(f"📂 Checkpoint saved. Resume with: reader convert --file \"{file_path}\" --batch-mode")
                            raise RuntimeError(f"Processing failed on chunk {i+1}: {error_msg}")
        
        # Final checkpoint save
        self._save_checkpoint(
            file_path, total_chunks, total_chunks,
            audio_segments, processing_config
        )
        
        print(f"✅ Processing complete: {len(audio_segments)} segments generated")
        
        # Cleanup checkpoint if requested
        if self.config.cleanup_on_completion and len(audio_segments) == total_chunks:
            print(f"🧹 Cleaning up checkpoint files...")
            self.checkpoint_manager.clear_checkpoint(file_path)
        
        return audio_segments
    
    def _save_checkpoint(self, file_path: Path, chunks_completed: int,
                        total_chunks: int, audio_segments: List[bytes],
                        processing_config: Dict[str, Any]) -> None:
        """Save checkpoint with error handling."""
        try:
            self.checkpoint_manager.save_checkpoint(
                file_path, chunks_completed, total_chunks,
                audio_segments, processing_config
            )
        except Exception as e:
            print(f"⚠️ Warning: Failed to save checkpoint: {e}")
            # Continue processing even if checkpoint fails
    
    def _load_checkpoint_segments(self, checkpoint: ProcessingCheckpoint) -> List[bytes]:
        """Load audio segments from checkpoint."""
        audio_segments = []
        
        for i, segment_path in enumerate(checkpoint.audio_segments):
            try:
                with open(segment_path, 'rb') as f:
                    audio_data = f.read()
                audio_segments.append(audio_data)
            except Exception as e:
                print(f"⚠️ Warning: Failed to load segment {i}: {e}")
                # Could implement segment recovery here
                continue
        
        return audio_segments
    
    def get_processing_status(self, file_path: Path) -> Dict[str, Any]:
        """Get current processing status for a file."""
        checkpoint = self.checkpoint_manager.load_checkpoint(file_path)
        
        if not checkpoint:
            return {
                'has_checkpoint': False,
                'status': 'not_started'
            }
        
        return {
            'has_checkpoint': True,
            'status': 'in_progress' if checkpoint.chunks_completed < checkpoint.total_chunks else 'completed',
            'progress': {
                'completed': checkpoint.chunks_completed,
                'total': checkpoint.total_chunks,
                'percent': checkpoint.get_progress_percent()
            },
            'timestamp': checkpoint.timestamp,
            'age_hours': (time.time() - checkpoint.timestamp) / 3600
        }
    
    def list_all_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints."""
        return self.checkpoint_manager.list_checkpoints()
    
    def cleanup_checkpoint(self, file_path: Path) -> bool:
        """Manually cleanup checkpoint for a file."""
        try:
            self.checkpoint_manager.clear_checkpoint(file_path)
            print(f"🧹 Cleaned up checkpoint for {file_path.name}")
            return True
        except Exception as e:
            print(f"❌ Failed to cleanup checkpoint: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return self.checkpoint_manager.get_checkpoint_summary()
    
    def _cleanup_old_segment_files(self, file_path: Path, keep_from_chunk: int) -> None:
        """Clean up old segment files that are no longer needed."""
        try:
            segments_dir = self.checkpoint_manager.segments_dir
            file_stem = file_path.stem
            
            # Find all segment files for this source file
            pattern = f"{file_stem}_segment_*.wav"
            segment_files = list(segments_dir.glob(pattern))
            
            cleaned_count = 0
            for segment_file in segment_files:
                try:
                    # Extract chunk number from filename
                    name_parts = segment_file.stem.split('_segment_')
                    if len(name_parts) == 2:
                        chunk_num = int(name_parts[1])
                        
                        # Remove if before the keep_from_chunk threshold
                        if chunk_num < keep_from_chunk:
                            segment_file.unlink()
                            cleaned_count += 1
                            
                except (ValueError, IndexError):
                    # Skip files with unexpected naming
                    continue
            
            if cleaned_count > 0:
                print(f"🧹 Cleaned up {cleaned_count} old segment files")
                
        except Exception as e:
            print(f"Warning: Failed to clean up old segments: {e}")


def _validate_chunk_input(chunk_text: str, chunk_idx: int, total_chunks: int) -> bool:
    """Validate chunk input to prevent common errors."""
    if not isinstance(chunk_text, str):
        print(f"⚠️ Warning: Chunk {chunk_idx} is not a string, skipping")
        return False
    
    if len(chunk_text.strip()) == 0:
        return True  # Empty chunks are OK, will generate silence
    
    if len(chunk_text) > 1000:  # Very long chunk might cause issues
        print(f"⚠️ Warning: Chunk {chunk_idx} is very long ({len(chunk_text)} chars)")
    
    return True


def _handle_tts_error(error: Exception, chunk_idx: int, chunk_text: str) -> str:
    """Analyze TTS errors and provide helpful error messages."""
    error_str = str(error).lower()
    
    if "phonemes are too long" in error_str:
        return f"Chunk {chunk_idx} exceeds phoneme limit. Try smaller chunk size."
    elif "voice" in error_str and "not found" in error_str:
        return f"Voice not available for chunk {chunk_idx}. Check voice configuration."
    elif "timeout" in error_str or "connection" in error_str:
        return f"Network/timeout error on chunk {chunk_idx}. Will retry."
    elif "memory" in error_str or "allocation" in error_str:
        return f"Memory error on chunk {chunk_idx}. System may be overloaded."
    else:
        return f"TTS error on chunk {chunk_idx}: {str(error)[:100]}"


def create_chunk_processor(tts_engine, voice_blend: Dict[str, float], speed: float):
    """Create a chunk processor function for the robust processor."""
    
    def process_chunk(chunk_text: str, chunk_idx: int, total_chunks: int) -> bytes:
        """Process a single text chunk to audio with error prevention."""
        # Validate input first
        if not _validate_chunk_input(chunk_text, chunk_idx, total_chunks):
            raise ValueError(f"Invalid chunk input at index {chunk_idx}")
        
        if not chunk_text.strip():
            # Return silence for empty chunks
            import wave
            import io
            
            # Create 0.1 second of silence
            sample_rate = 22050
            silence_samples = int(0.1 * sample_rate)
            silence_data = b'\x00\x00' * silence_samples
            
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(silence_data)
            
            wav_buffer.seek(0)
            return wav_buffer.read()
        
        try:
            # Use the TTS engine to synthesize audio
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
            
            # Replace problematic characters that might confuse TTS
            clean_text = clean_text.replace('\u00a0', ' ')  # Non-breaking space
            clean_text = clean_text.replace('\u2013', '-')  # En dash
            clean_text = clean_text.replace('\u2014', '-')  # Em dash
            clean_text = clean_text.replace('\u2019', "'")  # Right single quote
            clean_text = clean_text.replace('\u201c', '"')  # Left double quote
            clean_text = clean_text.replace('\u201d', '"')  # Right double quote
            
            return tts_engine.synthesize(clean_text, voice_str, speed)
            
        except Exception as e:
            # Provide helpful error analysis
            error_msg = _handle_tts_error(e, chunk_idx, chunk_text)
            raise RuntimeError(error_msg) from e
    
    return process_chunk