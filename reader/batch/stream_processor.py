"""Simple streaming processor with efficient checkpoints."""
import json
import time
import psutil
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Callable
from dataclasses import dataclass, asdict


@dataclass
class StreamCheckpoint:
    """Simple checkpoint for streaming conversion."""
    file_path: str
    current_chunk: int
    total_chunks: int
    output_size: int
    settings_hash: str
    timestamp: float


class StreamProcessor:
    """Simple streaming processor that writes directly to output file."""
    
    def __init__(self, output_path: Path, chunk_delay: float = 0.1, 
                 max_cpu_percent: float = 85.0, checkpoint_interval: int = 25):
        self.output_path = output_path
        self.chunk_delay = chunk_delay
        self.max_cpu_percent = max_cpu_percent
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_path = output_path.with_suffix('.checkpoint')
        self.mp3_batch_size = 4  # Process 4 chunks per MP3 conversion batch
        self.audio_buffer = []  # Buffer for batch MP3 conversion
        
    def process_with_stream(self, file_path: Path, text_chunks: List[str],
                           chunk_processor: Callable[[str, int, int], bytes],
                           processing_config: Dict[str, Any]) -> Path:
        """Process chunks and stream directly to output file."""
        total_chunks = len(text_chunks)
        settings_hash = self._get_settings_hash(processing_config)
        
        # Check for existing checkpoint
        start_chunk, output_size = self._load_checkpoint(file_path, total_chunks, settings_hash)
        
        print(f"🎯 Neural Engine stream processing {file_path.name} ({total_chunks} chunks, 48k mono MP3)")
        if start_chunk > 0:
            print(f"📂 Resuming from chunk {start_chunk} (file size: {output_size/1024/1024:.1f}MB)")
        
        # Open output file for appending
        mode = 'ab' if start_chunk > 0 else 'wb'
        with open(self.output_path, mode) as output_file:
            # Sequential processing optimized for Neural Engine
            self._process_chunks_sequential(output_file, text_chunks, chunk_processor, start_chunk, total_chunks, file_path, settings_hash)
            
            # Finalize any remaining MP3 batches
            self._finalize_mp3_processing(output_file)
        
        # Clean up checkpoint on completion
        self._cleanup_checkpoint()
        
        print(f"✅ Stream processing complete: {self.output_path}")
        return self.output_path
    
    def _process_chunks_sequential(self, output_file, text_chunks: List[str], 
                                 chunk_processor: Callable, start_chunk: int, 
                                 total_chunks: int, file_path: Path, settings_hash: str):
        """Sequential chunk processing (for Neural Engine compatibility)."""
        import time
        start_time = time.time()
        
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
            
            print(f"🧠 Chunk {i+1}/{total_chunks} ({progress:.1f}%){eta_str}", flush=True)
            
            # Process chunk
            audio_data = chunk_processor(chunk_text, i, total_chunks)
            
            # Convert and write
            self._convert_and_write_chunk(output_file, audio_data)
            
            # Thermal management disabled for maximum speed
            # Note: CPU usage > 100% is normal on multi-core systems
            # if cpu_usage > self.max_cpu_percent:
            #     extra_delay = min(5.0, (cpu_usage - self.max_cpu_percent) * 0.1)
            #     print(f"🚨 High CPU ({cpu_usage:.1f}%) - adding {extra_delay:.1f}s delay", flush=True)
            #     time.sleep(extra_delay)
            
            # Chunk delay disabled for maximum speed
            # if self.chunk_delay > 0:
            #     time.sleep(self.chunk_delay)
            
            # Save checkpoint periodically
            if (i + 1) % self.checkpoint_interval == 0:
                current_size = output_file.tell()
                self._save_checkpoint(file_path, i + 1, total_chunks, current_size, settings_hash)
    
    def _convert_and_write_chunk(self, output_file, audio_data: bytes):
        """Convert chunk to MP3 and write to file (with batching optimization)."""
        if self.output_path.suffix.lower() == '.mp3':
            # Add to batch buffer
            self.audio_buffer.append(audio_data)
            
            # Process batch when full
            if len(self.audio_buffer) >= self.mp3_batch_size:
                self._process_mp3_batch(output_file)
        else:
            # Direct write for WAV
            output_file.write(audio_data)
            output_file.flush()
    
    def _process_mp3_batch(self, output_file):
        """Process multiple audio chunks as a batch for MP3 conversion."""
        if not self.audio_buffer:
            return
            
        try:
            from ..processors.ffmpeg_processor import FFmpegAudioProcessor
            import tempfile
            
            # Combine all buffered audio data
            combined_audio = b''.join(self.audio_buffer)
            
            # Create temp WAV file for combined audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav.write(combined_audio)
                temp_wav_path = Path(temp_wav.name)
            
            # Convert to MP3
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                temp_mp3_path = Path(temp_mp3.name)
            
            processor = FFmpegAudioProcessor()
            processor.convert_format(temp_wav_path, temp_mp3_path, 'mp3')
            
            # Read compressed MP3 data
            with open(temp_mp3_path, 'rb') as f:
                mp3_data = f.read()
            
            # Clean up temp files
            temp_wav_path.unlink(missing_ok=True)
            temp_mp3_path.unlink(missing_ok=True)
            
            # Write compressed data
            output_file.write(mp3_data)
            output_file.flush()
            
            print(f"🎵 Batch converted {len(self.audio_buffer)} chunks to MP3", flush=True)
            
        except Exception as e:
            print(f"⚠️ Batch MP3 compression failed: {e}, writing WAV chunks", flush=True)
            # Fallback: write individual WAV chunks
            for audio_data in self.audio_buffer:
                output_file.write(audio_data)
            output_file.flush()
        
        # Clear buffer
        self.audio_buffer.clear()
    
    def _finalize_mp3_processing(self, output_file):
        """Process any remaining audio chunks in buffer."""
        if self.audio_buffer and self.output_path.suffix.lower() == '.mp3':
            print(f"🎵 Processing final batch of {len(self.audio_buffer)} chunks", flush=True)
            self._process_mp3_batch(output_file)
    
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
            
            checkpoint = StreamCheckpoint(**data)
            
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
        checkpoint = StreamCheckpoint(
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