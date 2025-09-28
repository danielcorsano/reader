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
    
    def __init__(self, output_path: Path, chunk_delay: float = 1.0, 
                 max_cpu_percent: float = 75.0, checkpoint_interval: int = 25):
        self.output_path = output_path
        self.chunk_delay = chunk_delay
        self.max_cpu_percent = max_cpu_percent
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_path = output_path.with_suffix('.checkpoint')
        
    def process_with_stream(self, file_path: Path, text_chunks: List[str],
                           chunk_processor: Callable[[str, int, int], bytes],
                           processing_config: Dict[str, Any]) -> Path:
        """Process chunks and stream directly to output file."""
        total_chunks = len(text_chunks)
        settings_hash = self._get_settings_hash(processing_config)
        
        # Check for existing checkpoint
        start_chunk, output_size = self._load_checkpoint(file_path, total_chunks, settings_hash)
        
        print(f"🎯 Stream processing {file_path.name} ({total_chunks} chunks)")
        if start_chunk > 0:
            print(f"📂 Resuming from chunk {start_chunk} (file size: {output_size/1024/1024:.1f}MB)")
        
        # Open output file for appending
        mode = 'ab' if start_chunk > 0 else 'wb'
        with open(self.output_path, mode) as output_file:
            # Process chunks
            for i in range(start_chunk, total_chunks):
                chunk_text = text_chunks[i]
                
                # CPU monitoring and thermal management
                cpu_usage = psutil.cpu_percent(interval=0.1)
                progress = ((i + 1) / total_chunks) * 100
                
                print(f"🔄 Processing chunk {i+1}/{total_chunks} ({progress:.1f}%) CPU: {cpu_usage:.1f}%", flush=True)
                
                # Process chunk
                audio_data = chunk_processor(chunk_text, i, total_chunks)
                
                # Write immediately to file
                output_file.write(audio_data)
                output_file.flush()  # Ensure data is written
                
                # Thermal management
                if cpu_usage > self.max_cpu_percent:
                    extra_delay = min(5.0, (cpu_usage - self.max_cpu_percent) * 0.1)
                    print(f"🚨 High CPU ({cpu_usage:.1f}%) - adding {extra_delay:.1f}s delay", flush=True)
                    time.sleep(extra_delay)
                
                if self.chunk_delay > 0:
                    time.sleep(self.chunk_delay)
                
                # Save checkpoint periodically
                if (i + 1) % self.checkpoint_interval == 0:
                    current_size = output_file.tell()
                    self._save_checkpoint(file_path, i + 1, total_chunks, current_size, settings_hash)
        
        # Clean up checkpoint on completion
        self._cleanup_checkpoint()
        
        print(f"✅ Stream processing complete: {self.output_path}")
        return self.output_path
    
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