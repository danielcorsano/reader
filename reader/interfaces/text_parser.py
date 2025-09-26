"""Abstract base class for text parsers."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class ParsedContent:
    """Container for parsed text content."""
    
    def __init__(
        self,
        title: str,
        content: str,
        chapters: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.content = content
        self.chapters = chapters or []
        self.metadata = metadata or {}


class TextParser(ABC):
    """Abstract base class for text file parsers."""
    
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if parser can handle this file type
        """
        pass
    
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedContent:
        """
        Parse text content from file.
        
        Args:
            file_path: Path to file to parse
            
        Returns:
            ParsedContent object with extracted text and metadata
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of file extensions this parser supports.
        
        Returns:
            List of file extensions (e.g., ['.epub', '.txt'])
        """
        pass