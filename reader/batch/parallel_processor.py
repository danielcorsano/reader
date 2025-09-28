"""Intelligent parallel processing for TTS conversion with thermal management."""
import time
import psutil
from pathlib import Path
from typing import List, Dict, Any, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import threading

from .robust_processor import BatchConfig


@dataclass
class ParallelConfig:
    """Configuration for parallel processing."""
    max_workers: int = 8  # Conservative for M3 MacBook Pro thermal management
    batch_size: int = 4   # Process chunks in small batches
    cpu_threshold: float = 75.0  # Reduce workers if CPU usage exceeds this
    memory_threshold_gb: float = 8.0  # Reduce workers if memory exceeds this
    thermal_monitoring: bool = True  # Enable thermal monitoring


class IntelligentParallelProcessor:
    """Intelligent parallel processor with adaptive worker management."""
    
    def __init__(self, parallel_config: ParallelConfig, batch_config: BatchConfig):
        self.parallel_config = parallel_config
        self.batch_config = batch_config
        self.current_workers = parallel_config.max_workers
        self.worker_lock = threading.Lock()
        self.stats = {
            'chunks_processed': 0,
            'total_processing_time': 0.0,
            'thermal_throttles': 0,
            'worker_adjustments': 0
        }
    
    def process_chunks_parallel(self, 
                              chunk_processor: Callable[[str, int, int], bytes],
                              text_chunks: List[str],
                              start_chunk: int = 0) -> List[bytes]:
        """Process text chunks in parallel with intelligent load balancing."""
        total_chunks = len(text_chunks)
        audio_segments = [None] * total_chunks  # Pre-allocate results list
        
        print(f"🚀 Starting parallel processing with {self.current_workers} workers", flush=True)
        
        # Process chunks in batches to manage memory and thermal load
        for batch_start in range(start_chunk, total_chunks, self.parallel_config.batch_size):
            batch_end = min(batch_start + self.parallel_config.batch_size, total_chunks)
            batch_chunks = text_chunks[batch_start:batch_end]
            
            # Check system resources before each batch
            self._adapt_worker_count()
            
            # Process batch in parallel
            batch_results = self._process_batch_parallel(
                chunk_processor, batch_chunks, batch_start, total_chunks
            )
            
            # Store results in correct positions
            for i, result in enumerate(batch_results):
                audio_segments[batch_start + i] = result
            
            # Thermal management between batches
            if self.batch_config.thermal_management:
                self._thermal_pause_between_batches(batch_start, total_chunks)
        
        # Filter out None values (shouldn't happen but safety check)
        return [segment for segment in audio_segments if segment is not None]
    
    def _process_batch_parallel(self,
                               chunk_processor: Callable[[str, int, int], bytes],
                               batch_chunks: List[str],
                               batch_start: int,
                               total_chunks: int) -> List[bytes]:
        """Process a batch of chunks in parallel."""
        batch_results = [None] * len(batch_chunks)
        
        with ThreadPoolExecutor(max_workers=self.current_workers) as executor:
            # Submit all chunks in the batch
            future_to_index = {}
            for i, chunk_text in enumerate(batch_chunks):
                chunk_idx = batch_start + i
                future = executor.submit(
                    self._process_single_chunk_with_monitoring,
                    chunk_processor, chunk_text, chunk_idx, total_chunks
                )
                future_to_index[future] = i
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    batch_results[index] = result
                except Exception as e:
                    print(f"❌ Error processing chunk {batch_start + index}: {e}", flush=True)
                    # Create silence for failed chunks
                    batch_results[index] = self._create_silence()
        
        return batch_results
    
    def _process_single_chunk_with_monitoring(self,
                                            chunk_processor: Callable[[str, int, int], bytes],
                                            chunk_text: str,
                                            chunk_idx: int,
                                            total_chunks: int) -> bytes:
        """Process a single chunk with monitoring."""
        start_time = time.time()
        
        # Show progress
        progress_percent = ((chunk_idx + 1) / total_chunks) * 100
        print(f"🔄 Worker processing chunk {chunk_idx + 1}/{total_chunks} ({progress_percent:.1f}%)", flush=True)
        
        # Process the chunk
        result = chunk_processor(chunk_text, chunk_idx, total_chunks)
        
        # Update stats
        processing_time = time.time() - start_time
        with self.worker_lock:
            self.stats['chunks_processed'] += 1
            self.stats['total_processing_time'] += processing_time
        
        return result
    
    def _adapt_worker_count(self) -> None:
        """Adapt worker count based on system resources."""
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_usage = psutil.virtual_memory().used / (1024**3)  # GB
        
        with self.worker_lock:
            old_workers = self.current_workers
            
            # Reduce workers if CPU usage is too high
            if cpu_usage > self.parallel_config.cpu_threshold:
                self.current_workers = max(1, self.current_workers - 1)
                self.stats['thermal_throttles'] += 1
                print(f"🚨 High CPU usage ({cpu_usage:.1f}%) - reducing workers to {self.current_workers}", flush=True)
            
            # Reduce workers if memory usage is too high
            elif memory_usage > self.parallel_config.memory_threshold_gb:
                self.current_workers = max(1, self.current_workers - 1)
                print(f"🚨 High memory usage ({memory_usage:.1f}GB) - reducing workers to {self.current_workers}", flush=True)
            
            # Increase workers if resources are available and we're below max
            elif (cpu_usage < self.parallel_config.cpu_threshold * 0.7 and 
                  memory_usage < self.parallel_config.memory_threshold_gb * 0.7 and
                  self.current_workers < self.parallel_config.max_workers):
                self.current_workers = min(self.parallel_config.max_workers, self.current_workers + 1)
                print(f"📈 Resources available - increasing workers to {self.current_workers}", flush=True)
            
            if old_workers != self.current_workers:
                self.stats['worker_adjustments'] += 1
    
    def _thermal_pause_between_batches(self, batch_start: int, total_chunks: int) -> None:
        """Add thermal pause between batches."""
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # Standard pause
        pause_time = self.batch_config.chunk_delay_seconds
        
        # Extra pause if CPU is hot
        if cpu_usage > self.batch_config.max_cpu_usage_percent:
            extra_pause = min(5.0, (cpu_usage - self.batch_config.max_cpu_usage_percent) * 0.1)
            pause_time += extra_pause
            print(f"🌡️ Thermal management: {pause_time:.1f}s pause (CPU: {cpu_usage:.1f}%)", flush=True)
        else:
            print(f"⏸️ Batch pause: {pause_time:.1f}s (CPU: {cpu_usage:.1f}%)", flush=True)
        
        time.sleep(pause_time)
    
    def _create_silence(self, duration: float = 0.1) -> bytes:
        """Create silence for failed chunks."""
        import wave
        import io
        
        sample_rate = 22050
        silence_samples = int(duration * sample_rate)
        silence_data = b'\\x00\\x00' * silence_samples
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silence_data)
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        with self.worker_lock:
            avg_time = (self.stats['total_processing_time'] / max(1, self.stats['chunks_processed']))
            return {
                **self.stats,
                'average_chunk_time': avg_time,
                'current_workers': self.current_workers,
                'max_workers': self.parallel_config.max_workers
            }