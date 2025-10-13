"""Public API for programmatic access to Reader."""

from pathlib import Path
from typing import Optional, Dict, Any
from .cli import ReaderApp


class Reader:
    """Programmatic interface to Reader audiobook converter."""

    def __init__(self):
        """Initialize Reader instance."""
        self._app = ReaderApp()

    def convert(
        self,
        file_path: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        output_format: Optional[str] = None,
        character_voices: bool = False,
        character_config: Optional[str] = None,
        checkpoint_interval: int = 50,
        progress_style: str = "simple",
        debug: bool = False
    ) -> Path:
        """
        Convert text file to audiobook.

        Args:
            file_path: Path to input file (EPUB, PDF, TXT, etc.)
            voice: Voice ID (e.g., 'am_michael', 'af_sarah'). Defaults to config.
            speed: Speech speed multiplier (0.5-2.0). Defaults to config.
            output_format: Audio format ('mp3', 'wav', 'm4a', 'm4b'). Defaults to config.
            character_voices: Enable character-specific voices for dialogue
            character_config: Path to character voice mapping YAML file
            checkpoint_interval: Save progress every N chunks
            progress_style: Progress display ('simple', 'tqdm', 'rich', 'timeseries')
            debug: Enable debug logging

        Returns:
            Path to generated audiobook file

        Example:
            >>> reader = Reader()
            >>> output = reader.convert("mybook.epub")
            >>> print(f"Created: {output}")

            >>> # Advanced usage
            >>> output = reader.convert(
            ...     "mybook.epub",
            ...     voice="af_sarah",
            ...     speed=1.2,
            ...     character_voices=True,
            ...     progress_style="timeseries"
            ... )
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        char_config_path = Path(character_config) if character_config else None

        return self._app.convert_file(
            file_path=file_path,
            voice=voice,
            speed=speed,
            format=output_format,
            character_voices=character_voices,
            character_config=char_config_path,
            batch_mode=True,
            checkpoint_interval=checkpoint_interval,
            turbo_mode=False,
            debug=debug,
            progress_style=progress_style
        )

    def list_voices(self) -> Dict[str, Any]:
        """
        List available TTS voices.

        Returns:
            Dictionary of voice information by voice ID

        Example:
            >>> reader = Reader()
            >>> voices = reader.list_voices()
            >>> for voice_id, info in voices.items():
            ...     print(f"{voice_id}: {info['gender']}, {info['language']}")
        """
        engine = self._app.get_tts_engine()
        return engine.VOICES


def convert(
    file_path: str,
    voice: Optional[str] = None,
    speed: Optional[float] = None,
    output_format: Optional[str] = None,
    **kwargs
) -> Path:
    """
    Convenience function for simple conversions.

    Args:
        file_path: Path to input file
        voice: Voice ID (optional)
        speed: Speech speed (optional)
        output_format: Audio format (optional)
        **kwargs: Additional arguments (see Reader.convert)

    Returns:
        Path to generated audiobook

    Example:
        >>> import reader
        >>> output = reader.convert("mybook.epub")
        >>> output = reader.convert("mybook.epub", voice="af_sarah", speed=1.2)
    """
    reader_instance = Reader()
    return reader_instance.convert(
        file_path=file_path,
        voice=voice,
        speed=speed,
        output_format=output_format,
        **kwargs
    )


def list_voices() -> Dict[str, Any]:
    """
    Convenience function to list available voices.

    Returns:
        Dictionary of voice information

    Example:
        >>> import reader
        >>> voices = reader.list_voices()
    """
    reader_instance = Reader()
    return reader_instance.list_voices()
