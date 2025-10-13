"""Timeseries visualization progress display for Neural Engine processing."""
import time
import os
from collections import deque
from .neural_processor import ProgressDisplay

try:
    import plotext as plt
    PLOTEXT_AVAILABLE = True
except ImportError:
    PLOTEXT_AVAILABLE = False


class TimeseriesProgressDisplay(ProgressDisplay):
    """Timeseries visualization with ASCII charts showing processing speed over time."""

    def __init__(self, debug: bool = False):
        self.start_time = None
        self.speed_history = deque(maxlen=50)  # Keep last 50 data points
        self.time_history = deque(maxlen=50)
        self.last_update_time = None
        self.last_chunk = 0
        self.debug = debug
        
    def start(self, total_chunks: int, file_name: str):
        if not PLOTEXT_AVAILABLE:
            raise ImportError("Plotext is not available")
            
        self.start_time = time.time()
        self.last_update_time = self.start_time
        print(f"🎯 Neural Engine stream processing {file_name} ({total_chunks} chunks, 48k mono MP3)")
        print("📊 Real-time processing speed visualization:")
        
        # Initialize with zero speed
        self.speed_history.append(0.0)
        self.time_history.append(0.0)
    
    def update(self, current_chunk: int, total_chunks: int, elapsed_time: float, eta_seconds: float):
        # Debug: log update calls
        if self.debug:
            from pathlib import Path
            debug_log = Path("/Users/corsano/Documents/code/reader/checkpoint_debug.log")
            with open(debug_log, 'a') as f:
                f.write(f"TimeseriesProgressDisplay.update({current_chunk}/{total_chunks}) at {time.time()} (instance id: {id(self)})\n")

        current_time = time.time()
        progress_pct = (current_chunk / total_chunks) * 100

        # Calculate instantaneous speed (chunks per minute)
        if current_chunk > self.last_chunk and current_time > self.last_update_time:
            time_delta = current_time - self.last_update_time
            chunk_delta = current_chunk - self.last_chunk
            instant_speed = (chunk_delta / time_delta) * 60  # Convert to chunks per minute
        else:
            instant_speed = 0.0

        # Add to history (convert to minutes for display)
        relative_time = (current_time - self.start_time) / 60
        self.speed_history.append(instant_speed)
        self.time_history.append(relative_time)

        # Clear screen and draw updated chart
        os.system('clear' if os.name == 'posix' else 'cls')

        # Print header
        elapsed_mins = int(elapsed_time // 60)
        elapsed_secs = int(elapsed_time % 60)
        print(f"🎯 Neural Engine stream processing ({current_chunk}/{total_chunks} chunks)")
        print(f"📊 Progress: {progress_pct:.1f}% | Speed: {instant_speed:.1f} chunk/min | Elapsed: {elapsed_mins}m {elapsed_secs}s | ETA: {eta_seconds/60:.1f}m")
        print()

        # Draw timeseries chart
        if len(self.speed_history) > 1:
            plt.clear_data()
            plt.clear_figure()
            plt.plot(list(self.time_history), list(self.speed_history), marker="dot", color="cyan")
            plt.title("🚀 Processing Speed Over Time")
            plt.ylabel("Speed (chunks/min)")

            # Build custom x ticks with "Xm Ys" labels
            max_time = max(self.time_history)
            interval = 0.5 if max_time < 5 else 1  # 30s or 1min intervals
            ticks = [i * interval for i in range(int(max_time / interval) + 2)]
            labels = []
            for t in ticks:
                secs = int(t * 60)
                m, s = divmod(secs, 60)
                labels.append(f"{m}m {s}s" if s else f"{m}m")

            plt.xticks(ticks, labels)
            plt.xlabel("Time")
            plt.plotsize(80, 15)
            plt.theme("dark")
            plt.show()
            import sys
            sys.stdout.flush()  # Ensure chart is fully written before progress bar

        # Draw progress bar
        bar_width = 60
        filled_width = int((current_chunk / total_chunks) * bar_width)
        bar = "█" * filled_width + "░" * (bar_width - filled_width)
        print(f"Progress: [{bar}] {progress_pct:.1f}%")
        import sys
        sys.stdout.flush()  # Ensure progress bar is written before next clear
        
        # Update tracking variables
        self.last_update_time = current_time
        self.last_chunk = current_chunk
    
    def finish(self):
        if PLOTEXT_AVAILABLE:
            plt.clear_data()
            print("\n✅ Processing complete!")