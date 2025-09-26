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

# Phase 2 imports
try:
    from .engines.kokoro_engine import KokoroEngine
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False

try:
    from .analysis.emotion_detector import EmotionDetector
    from .analysis.ssml_generator import SSMLGenerator
    from .voices.character_mapper import CharacterVoiceMapper
    PHASE2_AVAILABLE = True
except ImportError:
    PHASE2_AVAILABLE = False


class ReaderApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the reader application."""
        self.config_manager = ConfigManager()
        self.tts_engine = self._initialize_tts_engine()
        
        # Initialize parsers
        self.parsers: List[TextParser] = [
            EPUBParser(),
            PDFParser(),
            PlainTextParser()
        ]
        
        # Phase 2 components (optional)
        self.emotion_detector = None
        self.ssml_generator = None
        self.character_mapper = None
        
        if PHASE2_AVAILABLE:
            try:
                self.emotion_detector = EmotionDetector()
                self.ssml_generator = SSMLGenerator()
                self.character_mapper = CharacterVoiceMapper(self.config_manager.get_config_dir())
            except Exception as e:
                print(f"Warning: Phase 2 features not available: {e}")
        
        # Ensure directories exist
        self.config_manager.get_text_dir().mkdir(exist_ok=True)
        self.config_manager.get_audio_dir().mkdir(exist_ok=True)
        self.config_manager.get_config_dir().mkdir(exist_ok=True)
    
    def _initialize_tts_engine(self):
        """Initialize TTS engine based on configuration."""
        tts_config = self.config_manager.get_tts_config()
        
        if tts_config.engine == "kokoro" and KOKORO_AVAILABLE:
            try:
                return KokoroEngine()
            except Exception as e:
                print(f"Warning: Could not initialize Kokoro engine: {e}")
                print("Falling back to pyttsx3...")
                return PyTTSX3Engine()
        else:
            return PyTTSX3Engine()
    
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
        format: Optional[str] = None,
        emotion_analysis: Optional[bool] = None,
        character_voices: Optional[bool] = None
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
        processing_config = self.config_manager.get_processing_config()
        
        # Override with command-line arguments
        if voice:
            tts_config.voice = voice
        if speed:
            tts_config.speed = speed
        if format:
            audio_config.format = format
        if emotion_analysis is not None:
            processing_config.emotion_analysis = emotion_analysis
        if character_voices is not None:
            processing_config.character_voices = character_voices
        
        # Phase 2: Character analysis
        if self.character_mapper and processing_config.character_voices:
            click.echo("Analyzing characters and dialogue...")
            voice_analysis = self.character_mapper.analyze_text_for_voices(parsed_content.content)
            
            if voice_analysis['new_characters']:
                click.echo(f"Found new characters: {', '.join(voice_analysis['new_characters'])}")
            
            if voice_analysis['detected_characters']:
                click.echo(f"Character voices: {voice_analysis['voice_assignments']}")
        
        # Generate audio with enhanced processing
        click.echo(f"Generating audio for '{parsed_content.title}'...")
        
        # Process content intelligently
        if processing_config.emotion_analysis and self.ssml_generator:
            # Process with emotion and character awareness
            audio_segments = self._convert_with_emotion_analysis(
                parsed_content, tts_config, processing_config
            )
        else:
            # Fallback to chunk-based processing
            audio_segments = self._convert_basic_chunks(
                parsed_content.content, tts_config, processing_config
            )
        
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
    
    def _convert_with_emotion_analysis(self, parsed_content, tts_config, processing_config):
        """Convert content with emotion analysis and smart acting."""
        audio_segments = []
        
        # Split into sentences for better emotion analysis
        sentences = self._split_into_sentences(parsed_content.content)
        
        with click.progressbar(sentences, label="Converting with emotion analysis") as bar:
            for sentence in bar:
                if sentence.strip():
                    # Analyze emotion
                    emotion_analysis = self.emotion_detector.analyze_emotion(sentence)
                    
                    # Generate SSML if supported
                    if hasattr(self.tts_engine, 'supports_ssml') and self.tts_engine.supports_ssml():
                        # Generate SSML with emotion-based prosody
                        ssml_text = self.ssml_generator.generate_ssml(sentence, emotion_analysis)
                        text_to_synthesize = ssml_text
                    else:
                        # Apply prosody hints to TTS parameters
                        text_to_synthesize = sentence
                        # Adjust speed based on emotion
                        emotion_speed = tts_config.speed * emotion_analysis.prosody_hints.get('rate', 1.0)
                    
                    # Determine voice (character mapping if available)
                    voice_to_use = tts_config.voice
                    if self.character_mapper and processing_config.character_voices:
                        # Simple character detection for this sentence
                        detected_chars = self.character_mapper.detect_characters_in_text(sentence)
                        if detected_chars:
                            char_name = list(detected_chars)[0]
                            char_voice = self.character_mapper.get_character_voice(char_name)
                            if char_voice:
                                voice_to_use = char_voice.voice_id
                    
                    # Synthesize with appropriate voice and emotion adjustments
                    audio_data = self.tts_engine.synthesize(
                        text=text_to_synthesize,
                        voice=voice_to_use,
                        speed=emotion_speed if 'emotion_speed' in locals() else tts_config.speed,
                        volume=tts_config.volume
                    )
                    audio_segments.append(audio_data)
        
        return audio_segments
    
    def _convert_basic_chunks(self, content, tts_config, processing_config):
        """Fallback chunk-based conversion (Phase 1 style)."""
        chunk_size = processing_config.chunk_size
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        audio_segments = []
        
        with click.progressbar(chunks, label="Converting to speech") as bar:
            for chunk in bar:
                if chunk.strip():
                    audio_data = self.tts_engine.synthesize(
                        text=chunk,
                        voice=tts_config.voice,
                        speed=tts_config.speed,
                        volume=tts_config.volume
                    )
                    audio_segments.append(audio_data)
        
        return audio_segments
    
    def _split_into_sentences(self, text):
        """Split text into sentences for emotion analysis."""
        import re
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


# CLI Commands
@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Reader: Convert text files to audiobooks."""
    pass


@cli.command()
@click.option('--voice', '-v', help='Voice to use for synthesis')
@click.option('--speed', '-s', type=float, help='Speech speed multiplier (e.g., 1.2)')
@click.option('--format', '-f', type=click.Choice(['wav']), help='Output audio format (Phase 1-2: WAV only)')
@click.option('--file', '-F', type=click.Path(exists=True), help='Convert specific file instead of scanning text/ folder')
@click.option('--engine', '-e', type=click.Choice(['pyttsx3', 'kokoro']), help='TTS engine to use')
@click.option('--emotion/--no-emotion', default=None, help='Enable/disable emotion analysis')
@click.option('--characters/--no-characters', default=None, help='Enable/disable character voice mapping')
def convert(voice, speed, format, file, engine, emotion, characters):
    """Convert text files in text/ folder to audiobooks."""
    app = ReaderApp()
    
    # Override engine if specified
    if engine:
        app.config_manager.update_tts_config(engine=engine)
        app.tts_engine = app._initialize_tts_engine()
    
    if file:
        # Convert specific file
        file_path = Path(file)
        try:
            output_path = app.convert_file(
                file_path, voice, speed, format, emotion, characters
            )
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
                output_path = app.convert_file(
                    file_path, voice, speed, format, emotion, characters
                )
                click.echo(f"✓ {file_path.name} -> {output_path.name}")
            except Exception as e:
                click.echo(f"✗ Error converting {file_path.name}: {e}", err=True)


@cli.command()
@click.option('--engine', type=click.Choice(['pyttsx3', 'kokoro', 'all']), default='all', help='Show voices for specific engine')
@click.option('--language', help='Filter by language (e.g., en-us, en-uk)')
@click.option('--gender', type=click.Choice(['male', 'female']), help='Filter by gender')
def voices(engine, language, gender):
    """List available TTS voices."""
    app = ReaderApp()
    
    engines_to_show = []
    if engine == 'all':
        engines_to_show.append(('pyttsx3', app.tts_engine if isinstance(app.tts_engine, PyTTSX3Engine) else PyTTSX3Engine()))
        if KOKORO_AVAILABLE:
            try:
                kokoro_engine = KokoroEngine() if not isinstance(app.tts_engine, KokoroEngine) else app.tts_engine
                engines_to_show.append(('kokoro', kokoro_engine))
            except:
                pass
    elif engine == 'kokoro' and KOKORO_AVAILABLE:
        try:
            kokoro_engine = KokoroEngine() if not isinstance(app.tts_engine, KokoroEngine) else app.tts_engine
            engines_to_show.append(('kokoro', kokoro_engine))
        except Exception as e:
            click.echo(f"Kokoro engine not available: {e}")
            return
    else:
        engines_to_show.append((engine, app.tts_engine))
    
    for engine_name, engine_obj in engines_to_show:
        click.echo(f"\n{engine_name.upper()} Voices:")
        click.echo("=" * (len(engine_name) + 8))
        
        available_voices = engine_obj.list_voices()
        
        # Apply filters
        filtered_voices = available_voices
        
        if hasattr(engine_obj, 'get_voices_by_language') and language:
            filtered_voices = engine_obj.get_voices_by_language(language)
        
        if hasattr(engine_obj, 'get_voices_by_gender') and gender:
            if language:
                # Filter further
                filtered_voices = [v for v in filtered_voices if v in engine_obj.get_voices_by_gender(gender)]
            else:
                filtered_voices = engine_obj.get_voices_by_gender(gender)
        
        for voice in filtered_voices:
            voice_info = engine_obj.get_voice_info(voice)
            click.echo(f"  - {voice}")
            
            if voice_info.get('gender') != 'unknown':
                click.echo(f"    Gender: {voice_info.get('gender', 'unknown')}")
            
            if voice_info.get('lang'):
                click.echo(f"    Language: {voice_info.get('lang', 'unknown')}")
        
        click.echo(f"  Total: {len(filtered_voices)} voices")


# New Phase 2 commands
@cli.group()
def characters():
    """Manage character voice mappings."""
    pass


@characters.command()
@click.argument('name')
@click.argument('voice_id')
@click.option('--gender', default='unknown', help='Character gender')
@click.option('--description', default='', help='Character description')
def add(name, voice_id, gender, description):
    """Add a character voice mapping."""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Character mapping not available. Install Phase 2 dependencies.")
        return
    
    app.character_mapper.add_character(name, voice_id, gender, description)
    click.echo(f"✓ Added character '{name}' with voice '{voice_id}'")


@characters.command()
@click.argument('name')
def remove(name):
    """Remove a character voice mapping."""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Character mapping not available. Install Phase 2 dependencies.")
        return
    
    if app.character_mapper.remove_character(name):
        click.echo(f"✓ Removed character '{name}'")
    else:
        click.echo(f"✗ Character '{name}' not found")


@characters.command()
def list():
    """List all character voice mappings."""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Character mapping not available. Install Phase 2 dependencies.")
        return
    
    characters_list = app.character_mapper.list_characters()
    if not characters_list:
        click.echo("No characters configured.")
        return
    
    click.echo("Character Voice Mappings:")
    for char_name in characters_list:
        char_voice = app.character_mapper.get_character_voice(char_name)
        if char_voice:
            click.echo(f"  {char_name}: {char_voice.voice_id} ({char_voice.gender})")
            if char_voice.description:
                click.echo(f"    {char_voice.description}")


@cli.group()
def blend():
    """Manage voice blending."""
    pass


@blend.command()
@click.argument('name')
@click.argument('voice_spec')  # e.g., "af_sarah:60,af_nicole:40"
@click.option('--description', default='', help='Blend description')
def create(name, voice_spec, description):
    """Create a voice blend. Format: voice1:weight1,voice2:weight2"""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Voice blending not available. Install Phase 2 dependencies.")
        return
    
    try:
        # Parse voice specification
        voice_weights = {}
        for part in voice_spec.split(','):
            voice, weight = part.split(':')
            voice_weights[voice.strip()] = float(weight.strip()) / 100.0
        
        blend_spec = app.character_mapper.create_voice_blend(name, voice_weights, description)
        click.echo(f"✓ Created voice blend '{name}': {blend_spec}")
        
    except Exception as e:
        click.echo(f"✗ Error creating blend: {e}", err=True)


@blend.command()
def list():
    """List all voice blends."""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Voice blending not available. Install Phase 2 dependencies.")
        return
    
    blends = app.character_mapper.list_voice_blends()
    if not blends:
        click.echo("No voice blends configured.")
        return
    
    click.echo("Voice Blends:")
    for blend_name in blends:
        blend = app.character_mapper.get_voice_blend(blend_name)
        if blend:
            click.echo(f"  {blend_name}: {blend.voices}")
            if blend.description:
                click.echo(f"    {blend.description}")


@cli.command()
@click.option('--voice', help='Set default voice')
@click.option('--speed', type=float, help='Set default speed')
@click.option('--format', type=click.Choice(['wav']), help='Set default audio format (Phase 1-2: WAV only)')
@click.option('--engine', type=click.Choice(['pyttsx3', 'kokoro']), help='Set default TTS engine')
@click.option('--emotion/--no-emotion', help='Enable/disable emotion analysis by default')
@click.option('--characters/--no-characters', help='Enable/disable character voices by default')
def config(voice, speed, format, engine, emotion, characters):
    """Configure default settings."""
    app = ReaderApp()
    
    # TTS configuration updates
    tts_updates = {}
    if voice:
        tts_updates['voice'] = voice
    if speed:
        tts_updates['speed'] = speed
    if engine:
        tts_updates['engine'] = engine
    
    if tts_updates:
        app.config_manager.update_tts_config(**tts_updates)
        click.echo("TTS configuration updated.")
    
    # Audio configuration updates
    if format:
        app.config_manager.update_audio_config(format=format)
        click.echo("Audio configuration updated.")
    
    # Processing configuration updates
    processing_updates = {}
    if emotion is not None:
        processing_updates['emotion_analysis'] = emotion
    if characters is not None:
        processing_updates['character_voices'] = characters
    
    if processing_updates:
        app.config_manager.update_processing_config(**processing_updates)
        click.echo("Processing configuration updated.")
    
    if not any([voice, speed, format, engine, emotion is not None, characters is not None]):
        # Display current config
        tts_config = app.config_manager.get_tts_config()
        audio_config = app.config_manager.get_audio_config()
        processing_config = app.config_manager.get_processing_config()
        
        click.echo("Current configuration:")
        click.echo(f"  Engine: {tts_config.engine}")
        click.echo(f"  Voice: {tts_config.voice or 'default'}")
        click.echo(f"  Speed: {tts_config.speed}")
        click.echo(f"  Volume: {tts_config.volume}")
        click.echo(f"  Audio format: {audio_config.format}")
        
        # Phase 2 settings
        if PHASE2_AVAILABLE:
            click.echo("  Phase 2 Features:")
            click.echo(f"    Emotion analysis: {processing_config.emotion_analysis}")
            click.echo(f"    Character voices: {processing_config.character_voices}")
            click.echo(f"    Smart acting: {processing_config.smart_acting}")


@cli.command()
def info():
    """Show application information and quick start guide."""
    app = ReaderApp()
    
    text_dir = app.config_manager.get_text_dir()
    audio_dir = app.config_manager.get_audio_dir()
    
    # Header
    phase = "Phase 2" if PHASE2_AVAILABLE else "Phase 1"
    click.echo(f"📖 Reader: Text-to-Audiobook CLI ({phase})")
    click.echo("=" * 50)
    
    # System info
    click.echo(f"📂 Text directory: {text_dir.absolute()}")
    click.echo(f"🔊 Audio directory: {audio_dir.absolute()}")
    
    # Count files
    text_files = app.find_text_files()
    try:
        audio_files = list(audio_dir.glob("*.wav"))
    except Exception:
        # Fallback if glob fails
        audio_files = []
    
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
    if PHASE2_AVAILABLE:
        click.echo("  reader convert --engine kokoro # Use neural TTS")
        click.echo("  reader convert --emotion    # Enable emotion analysis")
        click.echo("  reader convert --characters # Enable character voices")
    click.echo("  reader voices               # List available voices")
    click.echo("  reader config               # View/set preferences")
    
    if PHASE2_AVAILABLE:
        click.echo("\n🎭 Phase 2 Commands:")
        click.echo("  reader characters add NAME VOICE # Map character to voice")
        click.echo("  reader characters list     # Show character mappings")
        click.echo("  reader blend create NAME SPEC # Create voice blend")
        click.echo("  reader blend list           # Show voice blends")
    
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
    if PHASE2_AVAILABLE:
        click.echo("\n🎯 Phase 2 Features:")
        click.echo("  ✅ Neural TTS (Kokoro) with 48+ voices")
        click.echo("  ✅ Emotion detection and smart acting")
        click.echo("  ✅ Character voice mapping")
        click.echo("  ✅ Voice blending capabilities")
        click.echo("  ✅ SSML-based prosody control")
        click.echo("  ✅ Multi-language support")
        
        click.echo("\n🔮 Coming in Phase 3:")
        click.echo("  Professional audiobook formats (MP3, M4B)")
        click.echo("  Advanced dialogue detection")
        click.echo("  Batch processing with queues")
    else:
        click.echo("\n🎯 Phase 1 Features:")
        click.echo("  ✅ 5 file formats (EPUB, PDF, TXT, MD, RST)")
        click.echo("  ✅ System TTS with voice selection")
        click.echo("  ✅ WAV audio output")
        click.echo("  ✅ Automatic chapter detection")
        click.echo("  ✅ Configuration management")
        
        click.echo("\n🔮 Available Upgrades:")
        click.echo("  Phase 2: Neural TTS + emotion detection")
        click.echo("  Install: poetry add kokoro-onnx vaderSentiment")
    
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