"""Abstract base class for audio processors."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class AudioProcessor(ABC):
    """Abstract base class for audio processing operations."""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_audio_info(self, audio_path: Path) -> Dict[str, Any]:
        """
        Get information about an audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata and properties
        """
        pass