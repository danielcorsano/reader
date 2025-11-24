"""Batch processing system for converting multiple books."""
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import concurrent.futures
import threading
from enum import Enum

from ..config import ConfigManager
from ..parsers.epub_parser import EPUBParser
from ..parsers.pdf_parser import PDFParser
from ..parsers.text_parser import PlainTextParser

try:
    from ..engines.kokoro_engine import KokoroEngine
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False

try:
    from ..voices.character_mapper import CharacterVoiceMapper
    from ..chapters.chapter_manager import ChapterManager
    from ..processors.ffmpeg_processor import get_audio_processor
    PHASE_3_AVAILABLE = True
except ImportError:
    PHASE_3_AVAILABLE = False


class JobStatus(Enum):
    """Status of a batch job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """Represents a single conversion job in a batch."""
    id: str
    input_file: Path
    output_file: Path
    config: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert Path objects to strings
        data['input_file'] = str(self.input_file)
        data['output_file'] = str(self.output_file)
        data['status'] = self.status.value
        # Convert datetime objects to ISO strings
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchJob':
        """Create from dictionary."""
        # Convert strings back to Path objects
        data['input_file'] = Path(data['input_file'])
        data['output_file'] = Path(data['output_file'])
        data['status'] = JobStatus(data['status'])
        # Convert ISO strings back to datetime objects
        if data.get('start_time'):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)


@dataclass
class BatchResult:
    """Results from a batch processing operation."""
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    total_duration: float
    results: List[BatchJob]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_jobs == 0:
            return 0.0
        return (self.completed_jobs / self.total_jobs) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_jobs': self.total_jobs,
            'completed_jobs': self.completed_jobs,
            'failed_jobs': self.failed_jobs,
            'cancelled_jobs': self.cancelled_jobs,
            'total_duration': self.total_duration,
            'success_rate': self.success_rate,
            'results': [job.to_dict() for job in self.results]
        }


class BatchProcessor:
    """Processes multiple audiobook conversions in batch."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, max_workers: int = 2):
        """
        Initialize batch processor.
        
        Args:
            config_manager: Configuration manager instance
            max_workers: Maximum number of concurrent workers
        """
        self.config_manager = config_manager or ConfigManager()
        self.max_workers = max_workers
        self.jobs: List[BatchJob] = []
        self.is_running = False
        self.is_cancelled = False
        self._progress_callback: Optional[Callable[[BatchJob], None]] = None
        self._lock = threading.Lock()
        
        # Initialize components
        self._initialize_engines()
        self._initialize_parsers()
        
        # Phase 3 components
        if PHASE_3_AVAILABLE:
            self.chapter_manager = ChapterManager()
            self.audio_processor = get_audio_processor()
        else:
            self.chapter_manager = None
            self.audio_processor = None
    
    def _initialize_engines(self) -> None:
        """Initialize TTS engines."""
        self.engines = {}
        # Engines will be initialized on demand during processing
    
    def _initialize_parsers(self) -> None:
        """Initialize text parsers."""
        self.parsers = [
            EPUBParser(),
            PDFParser(),
            PlainTextParser()
        ]
    
    def add_job(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a conversion job to the batch.
        
        Args:
            input_file: Path to input file
            output_file: Path for output file (if None, auto-generated)
            config_overrides: Configuration overrides for this job
            
        Returns:
            Job ID
        """
        # Generate job ID
        job_id = f"job_{int(time.time())}_{len(self.jobs)}"
        
        # Auto-generate output file if not provided
        if output_file is None:
            audio_config = self.config_manager.get_audio_config()
            tts_config = self.config_manager.get_tts_config()
            processing_config = self.config_manager.get_processing_config()

            # Build filename: stem_voice[_settings].format
            stem = input_file.stem
            voice = tts_config.voice or "am_michael"
            parts = [stem, voice]

            # Add non-default settings
            settings = []
            if tts_config.speed != 1.0:
                settings.append(f"sp{tts_config.speed}".replace(".", "p"))
            if processing_config.character_voices:
                settings.append("chr")
            if audio_config.format != "mp3":
                settings.append(audio_config.format)

            if settings:
                parts.append("_".join(settings))

            filename = "_".join(parts)
            # Limit length
            if len(filename) > 200:
                filename = filename[:200]

            output_file = input_file.parent / f"{filename}.{audio_config.format}"
        
        # Merge configuration
        job_config = self._merge_job_config(config_overrides)
        
        # Create job
        job = BatchJob(
            id=job_id,
            input_file=input_file,
            output_file=output_file,
            config=job_config
        )
        
        with self._lock:
            self.jobs.append(job)
        
        return job_id
    
    def add_directory(
        self,
        input_dir: Path,
        output_dir: Optional[Path] = None,
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add all compatible files in a directory to the batch.
        
        Args:
            input_dir: Directory containing input files
            output_dir: Directory for output files (if None, same as input)
            recursive: Whether to search subdirectories
            file_patterns: File patterns to match (if None, uses defaults)
            
        Returns:
            List of job IDs created
        """
        if file_patterns is None:
            file_patterns = ['*.epub', '*.pdf', '*.txt', '*.md']
        
        if output_dir is None:
            output_dir = input_dir
        
        job_ids = []
        search_pattern = "**/*" if recursive else "*"
        
        for pattern in file_patterns:
            for input_file in input_dir.glob(f"{search_pattern}.{pattern.split('.')[-1]}"):
                if input_file.is_file():
                    # Let add_job generate the filename, then we'll move to output_dir
                    job_id = self.add_job(input_file, None)
                    # Update output path to use output_dir while preserving relative structure
                    job = self.get_job_status(job_id)
                    if job:
                        relative_path = input_file.relative_to(input_dir)
                        job.output_file = output_dir / relative_path.parent / job.output_file.name
                    job_ids.append(job_id)
        
        return job_ids
    
    def _merge_job_config(self, overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge job-specific configuration with global config."""
        base_config = {
            'tts': asdict(self.config_manager.get_tts_config()),
            'audio': asdict(self.config_manager.get_audio_config()),
            'processing': asdict(self.config_manager.get_processing_config())
        }
        
        if overrides:
            # Deep merge overrides
            for section, values in overrides.items():
                if section in base_config and isinstance(values, dict):
                    base_config[section].update(values)
                else:
                    base_config[section] = values
        
        return base_config
    
    def set_progress_callback(self, callback: Callable[[BatchJob], None]) -> None:
        """Set callback function for progress updates."""
        self._progress_callback = callback
    
    def process_batch(
        self,
        save_progress: bool = True,
        progress_file: Optional[Path] = None
    ) -> BatchResult:
        """
        Process all jobs in the batch.
        
        Args:
            save_progress: Whether to save progress to file
            progress_file: Path for progress file (if None, auto-generated)
            
        Returns:
            BatchResult with processing results
        """
        if self.is_running:
            raise RuntimeError("Batch processing is already running")
        
        self.is_running = True
        self.is_cancelled = False
        start_time = time.time()
        
        try:
            # Setup progress file
            if save_progress and progress_file is None:
                progress_file = Path(f"batch_progress_{int(start_time)}.json")
            
            # Process jobs with thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all jobs
                future_to_job = {}
                for job in self.jobs:
                    if not self.is_cancelled:
                        future = executor.submit(self._process_single_job, job)
                        future_to_job[future] = job
                
                # Wait for completion
                for future in concurrent.futures.as_completed(future_to_job):
                    if self.is_cancelled:
                        # Cancel remaining jobs
                        for f in future_to_job:
                            f.cancel()
                        break
                    
                    job = future_to_job[future]
                    try:
                        future.result()  # This will raise any exceptions from the job
                    except Exception as e:
                        with self._lock:
                            job.status = JobStatus.FAILED
                            job.error_message = str(e)
                            job.end_time = datetime.now()
                    
                    # Save progress if requested
                    if save_progress and progress_file:
                        self._save_progress(progress_file)
                    
                    # Call progress callback
                    if self._progress_callback:
                        try:
                            self._progress_callback(job)
                        except Exception as e:
                            print(f"Warning: Progress callback failed: {e}")
            
            # Calculate results
            total_duration = time.time() - start_time
            result = self._calculate_batch_result(total_duration)
            
            return result
        
        finally:
            self.is_running = False
    
    def _process_single_job(self, job: BatchJob) -> None:
        """Process a single conversion job."""
        with self._lock:
            job.status = JobStatus.RUNNING
            job.start_time = datetime.now()
            job.progress = 0.0
        
        try:
            # Update progress
            job.progress = 10.0
            
            # Parse input file
            text_content = self._parse_input_file(job.input_file)
            job.progress = 30.0
            
            # Initialize components based on configuration
            engine = self._get_engine_for_job(job)
            job.progress = 40.0
            
            # Process text (Phase 2/3 features)
            processed_content = self._process_text_content(text_content, job.config)
            job.progress = 60.0
            
            # Generate audio
            audio_data = self._generate_audio(processed_content, engine, job.config)
            job.progress = 80.0
            
            # Save audio with format conversion if needed
            self._save_audio_output(audio_data, job.output_file, job.config)
            job.progress = 100.0
            
            with self._lock:
                job.status = JobStatus.COMPLETED
                job.end_time = datetime.now()
                if job.start_time:
                    job.duration = (job.end_time - job.start_time).total_seconds()
        
        except Exception as e:
            with self._lock:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.end_time = datetime.now()
                if job.start_time:
                    job.duration = (job.end_time - job.start_time).total_seconds()
            raise
    
    def _parse_input_file(self, input_file: Path) -> str:
        """Parse input file and extract text content."""
        for parser in self.parsers:
            if parser.can_parse(input_file):
                return parser.parse(input_file)
        
        raise ValueError(f"No parser available for file: {input_file}")
    
    def _get_engine_for_job(self, job: BatchJob):
        """Get TTS engine for a specific job."""
        engine_name = job.config.get('tts', {}).get('engine', 'kokoro')

        if engine_name not in self.engines:
            print(f"❌ Error: Engine '{engine_name}' not available.")
            print("💡 Only kokoro engine supported. Limited storage? Try reader-small package.")
            raise ValueError(f"Unsupported engine: {engine_name}")

        return self.engines[engine_name]
    
    def _process_text_content(self, text: str, config: Dict[str, Any]) -> str:
        """Process text content with Phase 2/3 features if enabled."""
        # Text processing moved to NeuralProcessor for character voices and dialogue detection
        return text
    
    def _generate_audio(self, text: str, engine, config: Dict[str, Any]) -> bytes:
        """Generate audio from text using specified engine."""
        tts_config = config.get('tts', {})
        
        return engine.synthesize(
            text=text,
            voice=tts_config.get('voice'),
            speed=tts_config.get('speed', 1.0),
            volume=tts_config.get('volume', 1.0)
        )
    
    def _save_audio_output(self, audio_data: bytes, output_file: Path, config: Dict[str, Any]) -> None:
        """Save audio data to output file with format conversion if needed."""
        audio_config = config.get('audio', {})
        target_format = audio_config.get('format', 'wav')
        
        # Create output directory
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if target_format.lower() == 'wav':
            # Direct save for WAV
            with open(output_file, 'wb') as f:
                f.write(audio_data)
        else:
            # Need format conversion (Phase 3 feature)
            if self.audio_processor and PHASE_3_AVAILABLE:
                # Save as temp WAV first
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_wav = Path(temp_file.name)
                
                try:
                    # Convert to target format
                    self.audio_processor.convert_format(
                        temp_wav,
                        output_file.with_suffix(f'.{target_format}'),
                        target_format
                    )
                finally:
                    # Clean up temp file
                    temp_wav.unlink(missing_ok=True)
            else:
                # Fallback to WAV
                print(f"Warning: Format conversion not available, saving as WAV")
                wav_output = output_file.with_suffix('.wav')
                with open(wav_output, 'wb') as f:
                    f.write(audio_data)
    
    def _calculate_batch_result(self, total_duration: float) -> BatchResult:
        """Calculate batch processing results."""
        completed = sum(1 for job in self.jobs if job.status == JobStatus.COMPLETED)
        failed = sum(1 for job in self.jobs if job.status == JobStatus.FAILED)
        cancelled = sum(1 for job in self.jobs if job.status == JobStatus.CANCELLED)
        
        return BatchResult(
            total_jobs=len(self.jobs),
            completed_jobs=completed,
            failed_jobs=failed,
            cancelled_jobs=cancelled,
            total_duration=total_duration,
            results=self.jobs.copy()
        )
    
    def _save_progress(self, progress_file: Path) -> None:
        """Save current progress to file."""
        try:
            progress_data = {
                'timestamp': datetime.now().isoformat(),
                'total_jobs': len(self.jobs),
                'jobs': [job.to_dict() for job in self.jobs]
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Warning: Failed to save progress: {e}")
    
    def load_progress(self, progress_file: Path) -> None:
        """Load progress from file and resume batch."""
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            self.jobs = [BatchJob.from_dict(job_data) for job_data in progress_data['jobs']]
            print(f"Loaded {len(self.jobs)} jobs from progress file")
        
        except Exception as e:
            raise RuntimeError(f"Failed to load progress file: {e}")
    
    def cancel_batch(self) -> None:
        """Cancel the current batch processing."""
        self.is_cancelled = True
        
        # Mark pending jobs as cancelled
        with self._lock:
            for job in self.jobs:
                if job.status == JobStatus.PENDING:
                    job.status = JobStatus.CANCELLED
    
    def clear_jobs(self) -> None:
        """Clear all jobs from the batch."""
        if self.is_running:
            raise RuntimeError("Cannot clear jobs while batch is running")
        
        with self._lock:
            self.jobs.clear()
    
    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get status of a specific job."""
        with self._lock:
            for job in self.jobs:
                if job.id == job_id:
                    return job
        return None
    
    def get_batch_summary(self) -> Dict[str, Any]:
        """Get summary of current batch."""
        with self._lock:
            status_counts = {}
            for status in JobStatus:
                status_counts[status.value] = sum(1 for job in self.jobs if job.status == status)
            
            return {
                'total_jobs': len(self.jobs),
                'status_counts': status_counts,
                'is_running': self.is_running,
                'is_cancelled': self.is_cancelled
            }
    
    def export_results(self, output_file: Path, result: BatchResult) -> None:
        """Export batch results to file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if output_file.suffix.lower() == '.json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        else:
            # Export as text report
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("BATCH PROCESSING RESULTS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total Jobs: {result.total_jobs}\n")
                f.write(f"Completed: {result.completed_jobs}\n")
                f.write(f"Failed: {result.failed_jobs}\n")
                f.write(f"Cancelled: {result.cancelled_jobs}\n")
                f.write(f"Success Rate: {result.success_rate:.1f}%\n")
                f.write(f"Total Duration: {result.total_duration:.1f} seconds\n\n")
                
                f.write("JOB DETAILS\n")
                f.write("-" * 30 + "\n")
                for job in result.results:
                    f.write(f"\nJob ID: {job.id}\n")
                    f.write(f"Input: {job.input_file}\n")
                    f.write(f"Output: {job.output_file}\n")
                    f.write(f"Status: {job.status.value}\n")
                    if job.duration:
                        f.write(f"Duration: {job.duration:.1f}s\n")
                    if job.error_message:
                        f.write(f"Error: {job.error_message}\n")


def create_batch_processor(config_manager: Optional[ConfigManager] = None, max_workers: int = 2) -> BatchProcessor:
    """Create a batch processor instance."""
    return BatchProcessor(config_manager, max_workers)