"""Main CLI interface for the reader application."""
import click
from pathlib import Path
from typing import List, Optional
import sys

from .config import ConfigManager
from .engines.pyttsx3_engine import PyTTSX3Engine
from .parsers.epub_parser import EPUBParser
from .parsers.pdf_parser import PDFParser
from .parsers.text_parser import PlainTextParser
from .interfaces.text_parser import TextParser


class ReaderApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the reader application."""
        self.config_manager = ConfigManager()
        self.tts_engine = PyTTSX3Engine()
        
        # Initialize parsers
        self.parsers: List[TextParser] = [
            EPUBParser(),
            PDFParser(),
            PlainTextParser()
        ]
        
        # Ensure directories exist
        self.config_manager.get_text_dir().mkdir(exist_ok=True)
        self.config_manager.get_audio_dir().mkdir(exist_ok=True)
        self.config_manager.get_config_dir().mkdir(exist_ok=True)
    
    def get_parser_for_file(self, file_path: Path) -> Optional[TextParser]:
        """Get appropriate parser for file."""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None
    
    def find_text_files(self) -> List[Path]:
        """Find all supported text files in text directory."""
        text_dir = self.config_manager.get_text_dir()
        supported_files = []
        
        for file_path in text_dir.iterdir():
            if file_path.is_file() and self.get_parser_for_file(file_path):
                supported_files.append(file_path)
        
        return supported_files
    
    def convert_file(
        self,
        file_path: Path,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        format: Optional[str] = None
    ) -> Path:
        """Convert a single file to audiobook."""
        # Get parser
        parser = self.get_parser_for_file(file_path)
        if not parser:
            raise ValueError(f"No parser available for file: {file_path}")
        
        # Parse content
        click.echo(f"Parsing {file_path.name}...")
        parsed_content = parser.parse(file_path)
        
        # Get configuration
        tts_config = self.config_manager.get_tts_config()
        audio_config = self.config_manager.get_audio_config()
        
        # Override with command-line arguments
        if voice:
            tts_config.voice = voice
        if speed:
            tts_config.speed = speed
        if format:
            audio_config.format = format
        
        # Generate audio
        click.echo(f"Generating audio for '{parsed_content.title}'...")
        
        # Split content into chunks for progress tracking
        content = parsed_content.content
        chunk_size = self.config_manager.get_processing_config().chunk_size
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        audio_segments = []
        
        with click.progressbar(chunks, label="Converting to speech") as bar:
            for chunk in bar:
                if chunk.strip():  # Skip empty chunks
                    audio_data = self.tts_engine.synthesize(
                        text=chunk,
                        voice=tts_config.voice,
                        speed=tts_config.speed,
                        volume=tts_config.volume
                    )
                    audio_segments.append(audio_data)
        
        # Create output filename
        audio_dir = self.config_manager.get_audio_dir()
        output_filename = f"{parsed_content.title}.{audio_config.format}"
        output_path = audio_dir / output_filename
        
        # Phase 1: Simple concatenation for multiple segments
        if len(audio_segments) == 1:
            self.tts_engine.save_audio(audio_segments[0], output_path, audio_config.format)
        else:
            # For Phase 1, save each segment as separate file
            click.echo("Phase 1: Saving audio segments as separate files...")
            for i, segment in enumerate(audio_segments):
                segment_path = audio_dir / f"{parsed_content.title}_part_{i+1:03d}.wav"
                self.tts_engine.save_audio(segment, segment_path, "wav")
            
            # Save first segment as main file for now
            output_path = output_path.with_suffix('.wav')
            self.tts_engine.save_audio(audio_segments[0], output_path, "wav")
        
        # Phase 1: Skip metadata (requires complex audio libraries)
        if audio_config.add_metadata:
            click.echo("Phase 1: Metadata addition will be available in Phase 2+")
        
        click.echo(f"Audiobook saved to: {output_path}")
        return output_path


# CLI Commands
@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Reader: Convert text files to audiobooks."""
    pass


@cli.command()
@click.option('--voice', '-v', help='Voice to use for synthesis')
@click.option('--speed', '-s', type=float, help='Speech speed multiplier (e.g., 1.2)')
@click.option('--format', '-f', type=click.Choice(['wav']), help='Output audio format (Phase 1: WAV only)')
@click.option('--file', '-F', type=click.Path(exists=True), help='Convert specific file instead of scanning text/ folder')
def convert(voice, speed, format, file):
    """Convert text files in text/ folder to audiobooks."""
    app = ReaderApp()
    
    if file:
        # Convert specific file
        file_path = Path(file)
        try:
            output_path = app.convert_file(file_path, voice, speed, format)
            click.echo(f"✓ Conversion complete: {output_path}")
        except Exception as e:
            click.echo(f"✗ Error converting {file_path}: {e}", err=True)
            sys.exit(1)
    else:
        # Scan text directory
        text_files = app.find_text_files()
        
        if not text_files:
            click.echo("No supported text files found in text/ directory.")
            click.echo("Supported formats: .epub, .pdf, .txt, .md, .rst")
            return
        
        click.echo(f"Found {len(text_files)} file(s) to convert:")
        for file_path in text_files:
            click.echo(f"  - {file_path.name}")
        
        # Convert each file
        for file_path in text_files:
            try:
                output_path = app.convert_file(file_path, voice, speed, format)
                click.echo(f"✓ {file_path.name} -> {output_path.name}")
            except Exception as e:
                click.echo(f"✗ Error converting {file_path.name}: {e}", err=True)


@cli.command()
def voices():
    """List available TTS voices."""
    app = ReaderApp()
    available_voices = app.tts_engine.list_voices()
    
    click.echo("Available voices:")
    for voice in available_voices:
        voice_info = app.tts_engine.get_voice_info(voice)
        click.echo(f"  - {voice}")
        if voice_info.get('gender') != 'unknown':
            click.echo(f"    Gender: {voice_info.get('gender', 'unknown')}")


@cli.command()
@click.option('--voice', help='Set default voice')
@click.option('--speed', type=float, help='Set default speed')
@click.option('--format', type=click.Choice(['wav']), help='Set default audio format (Phase 1: WAV only)')
def config(voice, speed, format):
    """Configure default settings."""
    app = ReaderApp()
    
    updates = {}
    if voice:
        updates['voice'] = voice
    if speed:
        updates['speed'] = speed
    
    if updates:
        app.config_manager.update_tts_config(**updates)
        click.echo("TTS configuration updated.")
    
    if format:
        app.config_manager.update_audio_config(format=format)
        click.echo("Audio configuration updated.")
    
    if not any([voice, speed, format]):
        # Display current config
        tts_config = app.config_manager.get_tts_config()
        audio_config = app.config_manager.get_audio_config()
        
        click.echo("Current configuration:")
        click.echo(f"  Voice: {tts_config.voice or 'default'}")
        click.echo(f"  Speed: {tts_config.speed}")
        click.echo(f"  Volume: {tts_config.volume}")
        click.echo(f"  Audio format: {audio_config.format}")


@cli.command()
def info():
    """Show application information and quick start guide."""
    app = ReaderApp()
    
    text_dir = app.config_manager.get_text_dir()
    audio_dir = app.config_manager.get_audio_dir()
    
    # Header
    click.echo("📖 Reader: Text-to-Audiobook CLI (Phase 1)")
    click.echo("=" * 50)
    
    # System info
    click.echo(f"📂 Text directory: {text_dir.absolute()}")
    click.echo(f"🔊 Audio directory: {audio_dir.absolute()}")
    
    # Count files
    text_files = app.find_text_files()
    audio_files = list(audio_dir.glob("*.wav"))
    
    click.echo(f"📚 Text files found: {len(text_files)}")
    click.echo(f"🎵 Audio files: {len(audio_files)}")
    
    # Quick start
    click.echo("\n🚀 Quick Start:")
    click.echo("1. Add text files to text/ folder (.epub, .pdf, .txt, .md)")
    click.echo("2. Run: poetry run reader convert")
    click.echo("3. Find audiobooks in audio/ folder")
    
    # Basic commands
    click.echo("\n💻 Basic Commands:")
    click.echo("  reader convert              # Convert all text files")
    click.echo("  reader convert --voice Alex # Use specific voice")
    click.echo("  reader voices               # List available voices")
    click.echo("  reader config               # View/set preferences")
    
    # Configuration
    tts_config = app.config_manager.get_tts_config()
    audio_config = app.config_manager.get_audio_config()
    
    click.echo("\n⚙️ Current Settings:")
    click.echo(f"  Voice: {tts_config.voice or 'default'}")
    click.echo(f"  Speed: {tts_config.speed}x")
    click.echo(f"  Format: {audio_config.format.upper()}")
    
    # Documentation
    click.echo("\n📚 Documentation:")
    click.echo("  README.md        - Project overview and quick start")
    click.echo("  docs/USAGE.md    - Complete command reference")
    click.echo("  docs/EXAMPLES.md - Real-world examples and workflows")
    
    # Phase info
    click.echo("\n🎯 Phase 1 Features:")
    click.echo("  ✅ 5 file formats (EPUB, PDF, TXT, MD, RST)")
    click.echo("  ✅ System TTS with voice selection")
    click.echo("  ✅ WAV audio output")
    click.echo("  ✅ Automatic chapter detection")
    click.echo("  ✅ Configuration management")
    
    # Next phases
    click.echo("\n🔮 Coming Next:")
    click.echo("  Phase 2: Neural TTS (48 voices) + emotion detection")
    click.echo("  Phase 3: Professional features + MP3/M4B export")
    
    # Tips
    if len(text_files) == 0:
        click.echo("\n💡 Tip: Add text files to get started!")
        click.echo("  echo 'Hello world!' > text/hello.txt")
        click.echo("  poetry run reader convert")
    elif len(audio_files) == 0:
        click.echo("\n💡 Tip: Run 'reader convert' to create audiobooks!")
    else:
        click.echo("\n🎉 Great! You have text and audio files ready.")


if __name__ == "__main__":
    cli()