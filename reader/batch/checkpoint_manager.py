"""Checkpoint management for robust batch processing."""
import json
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import hashlib
import time


@dataclass
class ProcessingCheckpoint:
    """Represents a processing checkpoint for resuming work."""
    file_path: str
    chunks_completed: int
    total_chunks: int
    audio_segments: List[str]  # Paths to saved audio segments
    processing_config: Dict[str, Any]
    timestamp: float
    file_hash: str  # To detect if source file changed
    disk_usage_mb: float = 0.0  # Track checkpoint disk usage
    
    def get_progress_percent(self) -> float:
        """Get completion percentage."""
        if self.total_chunks == 0:
            return 0.0
        return (self.chunks_completed / self.total_chunks) * 100


class CheckpointManager:
    """Manages processing checkpoints for resumable batch operations."""
    
    def __init__(self, checkpoint_dir: Optional[Path] = None, max_checkpoint_size_gb: float = 2.0):
        """Initialize checkpoint manager."""
        if checkpoint_dir is None:
            checkpoint_dir = Path.cwd() / "checkpoints"
        
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Directory for storing audio segment files
        self.segments_dir = self.checkpoint_dir / "segments"
        self.segments_dir.mkdir(parents=True, exist_ok=True)
        
        # Checkpoint size management
        self.max_checkpoint_size_gb = max_checkpoint_size_gb
        self.max_segments_per_checkpoint = 200  # Limit segments to prevent huge checkpoints
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file to detect changes."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return "unknown"
    
    def _get_checkpoint_path(self, file_path: Path) -> Path:
        """Get checkpoint file path for a given source file."""
        # Create safe filename from source path
        safe_name = str(file_path).replace("/", "_").replace("\\", "_")
        return self.checkpoint_dir / f"{safe_name}.checkpoint"
    
    def save_checkpoint(self, file_path: Path, chunks_completed: int, 
                       total_chunks: int, audio_segments: List[bytes],
                       processing_config: Dict[str, Any]) -> None:
        """Save processing checkpoint with size management."""
        try:
            # Check if we should limit checkpoint size
            if len(audio_segments) > self.max_segments_per_checkpoint:
                print(f"⚠️ Checkpoint too large ({len(audio_segments)} segments). Using rolling checkpoint strategy.")
                # Keep only the most recent segments
                audio_segments = audio_segments[-self.max_segments_per_checkpoint:]
                # Adjust chunks_completed to match available segments
                chunks_completed = max(0, chunks_completed - (len(audio_segments) - self.max_segments_per_checkpoint))
            
            # Check current disk usage
            current_usage_gb = self._get_total_disk_usage() / (1024**3)
            if current_usage_gb > self.max_checkpoint_size_gb:
                print(f"⚠️ Checkpoint disk usage ({current_usage_gb:.1f}GB) exceeds limit ({self.max_checkpoint_size_gb}GB)")
                self._cleanup_old_segments()
            
            # Save audio segments to individual files
            segment_paths = []
            total_size = 0
            
            for i, audio_data in enumerate(audio_segments):
                segment_file = self.segments_dir / f"{file_path.stem}_segment_{chunks_completed-len(audio_segments)+i}.wav"
                with open(segment_file, 'wb') as f:
                    f.write(audio_data)
                segment_paths.append(str(segment_file))
                total_size += len(audio_data)
            
            # Calculate disk usage in MB
            disk_usage_mb = total_size / (1024 * 1024)
            
            # Create checkpoint
            checkpoint = ProcessingCheckpoint(
                file_path=str(file_path),
                chunks_completed=chunks_completed,
                total_chunks=total_chunks,
                audio_segments=segment_paths,
                processing_config=processing_config,
                timestamp=time.time(),
                file_hash=self._get_file_hash(file_path),
                disk_usage_mb=disk_usage_mb
            )
            
            # Save checkpoint metadata
            checkpoint_path = self._get_checkpoint_path(file_path)
            with open(checkpoint_path, 'w') as f:
                json.dump(asdict(checkpoint), f, indent=2)
            
            print(f"💾 Checkpoint saved: {chunks_completed}/{total_chunks} chunks ({disk_usage_mb:.1f}MB)")
            
        except Exception as e:
            print(f"Warning: Failed to save checkpoint: {e}")
    
    def load_checkpoint(self, file_path: Path) -> Optional[ProcessingCheckpoint]:
        """Load processing checkpoint if available."""
        checkpoint_path = self._get_checkpoint_path(file_path)
        
        if not checkpoint_path.exists():
            return None
        
        try:
            with open(checkpoint_path, 'r') as f:
                data = json.load(f)
            
            checkpoint = ProcessingCheckpoint(**data)
            
            # Verify file hasn't changed
            current_hash = self._get_file_hash(file_path)
            if checkpoint.file_hash != current_hash and current_hash != "unknown":
                print(f"⚠️ Source file {file_path.name} has changed since checkpoint. Starting fresh.")
                self.clear_checkpoint(file_path)
                return None
            
            # Verify segment files exist
            missing_segments = []
            for segment_path in checkpoint.audio_segments:
                if not Path(segment_path).exists():
                    missing_segments.append(segment_path)
            
            if missing_segments:
                print(f"⚠️ Missing checkpoint segments: {len(missing_segments)}. Starting fresh.")
                self.clear_checkpoint(file_path)
                return None
            
            print(f"📂 Found checkpoint: {checkpoint.chunks_completed}/{checkpoint.total_chunks} chunks completed ({checkpoint.get_progress_percent():.1f}%)")
            return checkpoint
            
        except Exception as e:
            print(f"Warning: Failed to load checkpoint: {e}")
            self.clear_checkpoint(file_path)
            return None
    
    def clear_checkpoint(self, file_path: Path) -> None:
        """Clear checkpoint and associated files."""
        try:
            checkpoint_path = self._get_checkpoint_path(file_path)
            
            # Try to load checkpoint to get segment paths
            if checkpoint_path.exists():
                try:
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                    checkpoint = ProcessingCheckpoint(**data)
                    
                    # Delete segment files
                    for segment_path in checkpoint.audio_segments:
                        try:
                            Path(segment_path).unlink(missing_ok=True)
                        except:
                            pass
                except:
                    pass
            
            # Delete checkpoint file
            checkpoint_path.unlink(missing_ok=True)
            
            # Clean up any orphaned segment files for this source
            pattern = f"{file_path.stem}_segment_*.wav"
            for segment_file in self.segments_dir.glob(pattern):
                segment_file.unlink(missing_ok=True)
                
        except Exception as e:
            print(f"Warning: Failed to clear checkpoint: {e}")
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints."""
        checkpoints = []
        
        for checkpoint_file in self.checkpoint_dir.glob("*.checkpoint"):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                
                checkpoint = ProcessingCheckpoint(**data)
                checkpoints.append({
                    'file': checkpoint.file_path,
                    'progress': f"{checkpoint.chunks_completed}/{checkpoint.total_chunks}",
                    'percent': checkpoint.get_progress_percent(),
                    'timestamp': checkpoint.timestamp,
                    'age_hours': (time.time() - checkpoint.timestamp) / 3600
                })
                
            except Exception:
                continue
        
        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x['timestamp'], reverse=True)
        return checkpoints
    
    def cleanup_old_checkpoints(self, max_age_hours: int = 24) -> None:
        """Clean up old checkpoints."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        for checkpoint_file in self.checkpoint_dir.glob("*.checkpoint"):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                
                if data.get('timestamp', 0) < cutoff_time:
                    checkpoint = ProcessingCheckpoint(**data)
                    # Clean up associated files
                    for segment_path in checkpoint.audio_segments:
                        Path(segment_path).unlink(missing_ok=True)
                    
                    checkpoint_file.unlink()
                    print(f"🧹 Cleaned up old checkpoint: {Path(data['file_path']).name}")
                    
            except Exception:
                continue
    
    def get_checkpoint_summary(self) -> Dict[str, Any]:
        """Get summary of checkpoint system status."""
        checkpoints = self.list_checkpoints()
        
        # Calculate disk usage
        total_size = 0
        segment_count = 0
        
        for segment_file in self.segments_dir.rglob("*.wav"):
            try:
                total_size += segment_file.stat().st_size
                segment_count += 1
            except:
                continue
        
        return {
            'active_checkpoints': len(checkpoints),
            'total_segments': segment_count,
            'disk_usage_mb': total_size / (1024 * 1024),
            'checkpoint_dir': str(self.checkpoint_dir),
            'recent_checkpoints': checkpoints[:5]  # Show 5 most recent
        }
    
    def _get_total_disk_usage(self) -> int:
        """Get total disk usage of all checkpoint files in bytes."""
        total_size = 0
        
        # Count checkpoint metadata files
        for checkpoint_file in self.checkpoint_dir.glob("*.checkpoint"):
            try:
                total_size += checkpoint_file.stat().st_size
            except:
                continue
        
        # Count segment files
        for segment_file in self.segments_dir.rglob("*.wav"):
            try:
                total_size += segment_file.stat().st_size
            except:
                continue
        
        return total_size
    
    def _cleanup_old_segments(self) -> None:
        """Clean up old segments to free disk space."""
        # Get all segment files with timestamps
        segment_files = []
        for segment_file in self.segments_dir.rglob("*.wav"):
            try:
                mtime = segment_file.stat().st_mtime
                size = segment_file.stat().st_size
                segment_files.append((segment_file, mtime, size))
            except:
                continue
        
        # Sort by modification time (oldest first)
        segment_files.sort(key=lambda x: x[1])
        
        # Remove oldest files until under size limit
        current_usage = self._get_total_disk_usage()
        target_usage = int(self.max_checkpoint_size_gb * 0.8 * 1024**3)  # 80% of limit
        
        for segment_file, mtime, size in segment_files:
            if current_usage <= target_usage:
                break
            
            try:
                segment_file.unlink()
                current_usage -= size
                print(f"🧹 Cleaned up old segment: {segment_file.name}")
            except:
                continue