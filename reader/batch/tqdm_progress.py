"""TQDM-based progress display for Neural Engine processing."""
import time
from .neural_processor import ProgressDisplay

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class TQDMProgressDisplay(ProgressDisplay):
    """TQDM progress bar display with ETA and processing speed."""
    
    def __init__(self):
        self.pbar = None
        self.start_time = None
        
    def start(self, total_chunks: int, file_name: str):
        if not TQDM_AVAILABLE:
            raise ImportError("TQDM is not available")
            
        self.start_time = time.time()
        print(f"🎯 Neural Engine stream processing {file_name} ({total_chunks} chunks, 48k mono MP3)")
        
        # Create TQDM progress bar with custom format
        self.pbar = tqdm(
            total=total_chunks,
            desc="🧠 Processing",
            unit="chunk",
            ncols=80,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
        )
    
    def update(self, current_chunk: int, total_chunks: int, elapsed_time: float, eta_seconds: float):
        if self.pbar is None:
            return

        # Update progress bar to current chunk
        self.pbar.n = current_chunk

        # Calculate processing speed (chunks per minute)
        if elapsed_time > 0:
            chunks_per_min = ((current_chunk - self.pbar.n + 1) / elapsed_time) * 60 if current_chunk > 1 else 0
            self.pbar.set_postfix({
                'speed': f'{chunks_per_min:.1f} chunk/min' if chunks_per_min > 0 else 'calculating...'
            })

        self.pbar.refresh()
    
    def finish(self):
        if self.pbar:
            self.pbar.close()
            self.pbar = None