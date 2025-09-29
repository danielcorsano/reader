"""Rich-based enhanced progress display for Neural Engine processing."""
import time
from .neural_processor import ProgressDisplay

try:
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn, SpinnerColumn
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class RichProgressDisplay(ProgressDisplay):
    """Rich enhanced progress display with beautiful formatting and metrics."""
    
    def __init__(self):
        self.progress = None
        self.task_id = None
        self.console = None
        self.start_time = None
        
    def start(self, total_chunks: int, file_name: str):
        if not RICH_AVAILABLE:
            raise ImportError("Rich is not available")
            
        self.start_time = time.time()
        self.console = Console()
        
        # Print header with Rich styling
        self.console.print(f"🎯 [bold cyan]Neural Engine stream processing[/bold cyan] {file_name}")
        self.console.print(f"   [dim]({total_chunks} chunks, 48k mono MP3)[/dim]")
        
        # Create Rich progress bar with custom columns
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]🧠 Processing"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("{task.completed}/{task.total} chunks"),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            TextColumn("•"),
            TextColumn("[green]{task.fields[speed]:.1f} chunk/s[/green]"),
            console=self.console,
            transient=False
        )
        
        self.progress.start()
        self.task_id = self.progress.add_task("processing", total=total_chunks, speed=0.0)
    
    def update(self, current_chunk: int, total_chunks: int, elapsed_time: float, eta_seconds: float):
        if self.progress is None or self.task_id is None:
            return
            
        # Calculate processing speed (chunks per second)
        speed = 0.0
        if elapsed_time > 0 and current_chunk > 1:
            speed = (current_chunk - 1) / elapsed_time
        
        # Update the progress bar
        self.progress.update(
            self.task_id,
            completed=current_chunk,
            speed=speed
        )
    
    def finish(self):
        if self.progress:
            self.progress.stop()
            self.progress = None
            self.task_id = None