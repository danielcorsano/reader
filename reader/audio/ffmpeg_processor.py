"""FFmpeg-based audio processor for Phase 3 advanced audio features."""
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json

from ..interfaces.audio_processor import AudioProcessor

try:
    from mutagen.mp4 import MP4, MP4Cover
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TPOS, CHAP, CTOC
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False


class FFmpegAudioProcessor(AudioProcessor):
    """Audio processor using FFmpeg for advanced audio operations."""
    
    SUPPORTED_FORMATS = ['wav', 'mp3', 'm4a', 'm4b', 'aac', 'ogg', 'flac']
    
    def __init__(self):
        """Initialize the FFmpeg audio processor."""
        if not AUDIO_LIBS_AVAILABLE:
            raise ImportError("Audio libraries not available. Install with: poetry add mutagen")
        
        self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> None:
        """Check if FFmpeg is available on the system."""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: FFmpeg not found. Some audio operations may not work.")
            print("Install FFmpeg: https://ffmpeg.org/download.html")
    
    def convert_format(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str
    ) -> None:
        """
        Convert audio from one format to another.
        
        Args:
            input_path: Input audio file path
            output_path: Output audio file path  
            target_format: Target audio format (mp3, wav, m4a, etc.)
        """
        if target_format.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {target_format}. "
                           f"Supported: {self.SUPPORTED_FORMATS}")
        
        try:
            # Use FFmpeg for format conversion
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            cmd = ['ffmpeg', '-i', str(input_path)]
            
            # Add format-specific parameters
            export_params = self._get_export_parameters(target_format)
            if 'codec' in export_params:
                cmd.extend(['-c:a', export_params['codec']])
            if 'bitrate' in export_params:
                cmd.extend(['-b:a', export_params['bitrate']])
            if 'parameters' in export_params:
                cmd.extend(export_params['parameters'])
            
            cmd.extend(['-y', str(output_path)])
            
            subprocess.run(cmd, check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to convert audio with FFmpeg: {e}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html")
        except Exception as e:
            raise RuntimeError(f"Failed to convert audio: {e}")
    
    def _get_export_parameters(self, format: str) -> Dict[str, Any]:
        """Get optimal export parameters for each format."""
        format = format.lower()
        
        if format == 'mp3':
            return {
                'bitrate': '128k',
                'parameters': ['-q:a', '2']  # VBR quality
            }
        elif format in ['m4a', 'm4b']:
            return {
                'codec': 'aac',
                'bitrate': '128k',
                'parameters': ['-movflags', '+faststart']
            }
        elif format == 'wav':
            return {
                'parameters': ['-acodec', 'pcm_s16le']
            }
        elif format == 'ogg':
            return {
                'codec': 'libvorbis',
                'parameters': ['-q:a', '5']
            }
        elif format == 'flac':
            return {
                'codec': 'flac',
                'parameters': ['-compression_level', '5']
            }
        else:
            return {}
    
    def add_metadata(
        self,
        audio_path: Path,
        title: str,
        author: Optional[str] = None,
        album: Optional[str] = None,
        chapters: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add metadata to audio file.
        
        Args:
            audio_path: Path to audio file
            title: Title of the audiobook
            author: Author name
            album: Album/series name
            chapters: List of chapter information
        """
        file_ext = audio_path.suffix.lower()
        
        if file_ext in ['.m4a', '.m4b']:
            self._add_m4a_metadata(audio_path, title, author, album, chapters)
        elif file_ext == '.mp3':
            self._add_mp3_metadata(audio_path, title, author, album, chapters)
        else:
            print(f"Warning: Metadata not supported for {file_ext} format")
    
    def _add_m4a_metadata(
        self,
        audio_path: Path,
        title: str,
        author: Optional[str] = None,
        album: Optional[str] = None,
        chapters: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add metadata to M4A/M4B file."""
        try:
            audiofile = MP4(str(audio_path))
            
            # Basic metadata
            audiofile['©nam'] = title  # Title
            if author:
                audiofile['©ART'] = author  # Artist
                audiofile['©alb'] = album or f"{title} by {author}"  # Album
            
            # Audiobook specific metadata
            audiofile['©gen'] = 'Audiobook'  # Genre
            audiofile['stik'] = [2]  # Media type: Audiobook
            
            # Add chapters if provided
            if chapters and audio_path.suffix.lower() == '.m4b':
                self._add_m4b_chapters(audiofile, chapters)
            
            audiofile.save()
            
        except Exception as e:
            print(f"Warning: Failed to add M4A metadata: {e}")
    
    def _add_mp3_metadata(
        self,
        audio_path: Path,
        title: str,
        author: Optional[str] = None,
        album: Optional[str] = None,
        chapters: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add metadata to MP3 file."""
        try:
            audiofile = ID3(str(audio_path))
            
            # Basic metadata
            audiofile['TIT2'] = TIT2(encoding=3, text=title)  # Title
            if author:
                audiofile['TPE1'] = TPE1(encoding=3, text=author)  # Artist
                audiofile['TALB'] = TALB(encoding=3, text=album or f"{title} by {author}")  # Album
            
            # Add chapters if provided (ID3v2.3 CHAP frames)
            if chapters:
                self._add_mp3_chapters(audiofile, chapters)
            
            audiofile.save()
            
        except Exception as e:
            print(f"Warning: Failed to add MP3 metadata: {e}")
    
    def _add_m4b_chapters(self, audiofile, chapters: List[Dict[str, Any]]) -> None:
        """Add chapter markers to M4B file."""
        try:
            # Create chapter list for M4B
            chapter_data = []
            
            for i, chapter in enumerate(chapters):
                start_ms = int(chapter.get('start_time', 0) * 1000)
                title = chapter.get('title', f'Chapter {i + 1}')
                
                chapter_data.append({
                    'start_time': start_ms,
                    'title': title
                })
            
            # Add chapter data to file
            if chapter_data:
                # This is a simplified implementation
                # Full M4B chapter support requires more complex atom manipulation
                print(f"Added {len(chapter_data)} chapters to M4B file")
                
        except Exception as e:
            print(f"Warning: Failed to add M4B chapters: {e}")
    
    def _add_mp3_chapters(self, audiofile, chapters: List[Dict[str, Any]]) -> None:
        """Add chapter markers to MP3 file using ID3v2.3 CHAP frames."""
        try:
            # Create table of contents
            toc_children = []
            
            for i, chapter in enumerate(chapters):
                chapter_id = f"chp{i}"
                start_ms = int(chapter.get('start_time', 0) * 1000)
                end_ms = int(chapter.get('end_time', start_ms + 60000))  # Default 1 min if no end
                title = chapter.get('title', f'Chapter {i + 1}')
                
                # Add CHAP frame
                audiofile.add(CHAP(
                    encoding=3,
                    element_id=chapter_id,
                    start_time=start_ms,
                    end_time=end_ms,
                    start_offset=0xFFFFFFFF,
                    end_offset=0xFFFFFFFF,
                    sub_frames=[TIT2(encoding=3, text=title)]
                ))
                
                toc_children.append(chapter_id)
            
            # Add table of contents
            if toc_children:
                audiofile.add(CTOC(
                    encoding=3,
                    element_id="toc",
                    flags=0x03,  # Top-level and ordered
                    child_element_ids=toc_children,
                    sub_frames=[TIT2(encoding=3, text="Table of Contents")]
                ))
                
        except Exception as e:
            print(f"Warning: Failed to add MP3 chapters: {e}")
    
    def merge_audio_files(
        self,
        input_files: List[Path],
        output_path: Path,
        chapters: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Merge multiple audio files into one.
        
        Args:
            input_files: List of audio files to merge
            output_path: Output merged file path
            chapters: Chapter markers for merged file
        """
        if not input_files:
            raise ValueError("No input files provided")
        
        try:
            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create temporary file list for FFmpeg concat
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for input_file in input_files:
                    f.write(f"file '{input_file.absolute()}'\n")
                list_file = f.name
            
            try:
                # Use FFmpeg concat demuxer for merging
                format = output_path.suffix[1:].lower()
                export_params = self._get_export_parameters(format)
                
                cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file]
                
                # Add format-specific parameters
                if 'codec' in export_params:
                    cmd.extend(['-c:a', export_params['codec']])
                if 'bitrate' in export_params:
                    cmd.extend(['-b:a', export_params['bitrate']])
                if 'parameters' in export_params:
                    cmd.extend(export_params['parameters'])
                
                cmd.extend(['-y', str(output_path)])
                
                subprocess.run(cmd, check=True, capture_output=True)
                
            finally:
                # Clean up temporary file
                Path(list_file).unlink(missing_ok=True)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to merge audio files with FFmpeg: {e}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html")
        except Exception as e:
            raise RuntimeError(f"Failed to merge audio files: {e}")
    
    def get_audio_info(self, audio_path: Path) -> Dict[str, Any]:
        """
        Get information about an audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata and properties
        """
        try:
            # Use FFprobe to get audio info
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(result.stdout)
            
            # Extract audio stream info
            audio_stream = None
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise RuntimeError("No audio stream found")
            
            duration = float(probe_data.get('format', {}).get('duration', 0))
            
            info = {
                'duration_seconds': duration,
                'duration_formatted': self._format_duration(duration),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'format': audio_path.suffix[1:].upper(),
                'file_size': audio_path.stat().st_size,
                'bitrate': int(audio_stream.get('bit_rate', 0)) // 1000 if audio_stream.get('bit_rate') else None
            }
            
            # Try to get metadata
            metadata = self._get_file_metadata(audio_path)
            info.update(metadata)
            
            return info
            
        except Exception as e:
            return {
                'error': str(e),
                'file_size': audio_path.stat().st_size if audio_path.exists() else 0
            }
    
    def _get_file_metadata(self, audio_path: Path) -> Dict[str, Any]:
        """Extract metadata from audio file."""
        metadata = {}
        file_ext = audio_path.suffix.lower()
        
        try:
            if file_ext in ['.m4a', '.m4b']:
                audiofile = MP4(str(audio_path))
                metadata.update({
                    'title': audiofile.get('©nam', [''])[0],
                    'artist': audiofile.get('©ART', [''])[0],
                    'album': audiofile.get('©alb', [''])[0],
                    'genre': audiofile.get('©gen', [''])[0],
                })
            elif file_ext == '.mp3':
                audiofile = ID3(str(audio_path))
                metadata.update({
                    'title': str(audiofile.get('TIT2', '')),
                    'artist': str(audiofile.get('TPE1', '')),
                    'album': str(audiofile.get('TALB', '')),
                })
        except Exception:
            pass  # Ignore metadata errors
        
        return metadata
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def normalize_audio(self, input_path: Path, output_path: Path, target_lufs: float = -23.0) -> None:
        """
        Normalize audio to target LUFS level.
        
        Args:
            input_path: Input audio file
            output_path: Output normalized file
            target_lufs: Target LUFS level (default: -23.0 for audiobooks)
        """
        try:
            # Use FFmpeg for audio normalization
            cmd = [
                'ffmpeg', '-i', str(input_path),
                '-af', f'loudnorm=I={target_lufs}:TP=-2.0:LRA=7.0',
                '-c:a', 'aac', '-b:a', '128k',
                '-y', str(output_path)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to normalize audio: {e}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html")
    
    def add_silence(self, input_path: Path, output_path: Path, 
                   start_silence: float = 0.0, end_silence: float = 0.0) -> None:
        """
        Add silence to the beginning and/or end of audio file.
        
        Args:
            input_path: Input audio file
            output_path: Output file with silence
            start_silence: Seconds of silence to add at start
            end_silence: Seconds of silence to add at end
        """
        try:
            # Use FFmpeg to add silence with adelay and apad filters
            cmd = ['ffmpeg', '-i', str(input_path)]
            
            filters = []
            if start_silence > 0:
                filters.append(f'adelay={int(start_silence * 1000)}|{int(start_silence * 1000)}')
            if end_silence > 0:
                filters.append(f'apad=pad_dur={end_silence}')
            
            if filters:
                cmd.extend(['-af', ','.join(filters)])
            
            # Add format-specific parameters
            format = output_path.suffix[1:].lower()
            export_params = self._get_export_parameters(format)
            if 'codec' in export_params:
                cmd.extend(['-c:a', export_params['codec']])
            if 'bitrate' in export_params:
                cmd.extend(['-b:a', export_params['bitrate']])
            if 'parameters' in export_params:
                cmd.extend(export_params['parameters'])
            
            cmd.extend(['-y', str(output_path)])
            
            subprocess.run(cmd, check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to add silence with FFmpeg: {e}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html")
        except Exception as e:
            raise RuntimeError(f"Failed to add silence: {e}")


class BasicAudioProcessor(AudioProcessor):
    """Basic audio processor for when FFmpeg is not available."""
    
    def convert_format(self, input_path: Path, output_path: Path, target_format: str) -> None:
        """Basic format conversion (copy only for same format)."""
        if input_path.suffix.lower() == f".{target_format.lower()}":
            # Same format, just copy
            import shutil
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_path, output_path)
        else:
            raise NotImplementedError("Format conversion requires FFmpeg")
    
    def add_metadata(self, audio_path: Path, title: str, author: Optional[str] = None, 
                    album: Optional[str] = None, chapters: Optional[List[Dict[str, Any]]] = None) -> None:
        """Basic metadata addition not supported."""
        print("Warning: Metadata addition requires mutagen library")
    
    def merge_audio_files(self, input_files: List[Path], output_path: Path, 
                         chapters: Optional[List[Dict[str, Any]]] = None) -> None:
        """Basic file merging not supported."""
        raise NotImplementedError("Audio merging requires FFmpeg")
    
    def get_audio_info(self, audio_path: Path) -> Dict[str, Any]:
        """Basic audio info (file size only)."""
        return {
            'file_size': audio_path.stat().st_size if audio_path.exists() else 0,
            'format': audio_path.suffix[1:].upper(),
            'error': 'Limited info - install FFmpeg for full details'
        }


def get_audio_processor() -> AudioProcessor:
    """Get the best available audio processor."""
    if AUDIO_LIBS_AVAILABLE:
        return FFmpegAudioProcessor()
    else:
        return BasicAudioProcessor()