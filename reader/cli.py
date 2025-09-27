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

# Phase 3 imports
try:
    from .analysis.dialogue_detector import DialogueDetector
    from .chapters.chapter_manager import ChapterManager
    from .audio.ffmpeg_processor import get_audio_processor
    from .voices.voice_previewer import get_voice_previewer
    from .batch.batch_processor import create_batch_processor
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False


class ReaderApp:
    """Main application class."""
    
    def __init__(self, init_tts=False):
        """Initialize the reader application."""
        self.config_manager = ConfigManager()
        self.tts_engine = None
        if init_tts:
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
        
        # Phase 3 components (optional)
        self.dialogue_detector = None
        self.chapter_manager = None
        self.audio_processor = None
        self.voice_previewer = None
        
        if PHASE2_AVAILABLE:
            try:
                self.emotion_detector = EmotionDetector()
                self.ssml_generator = SSMLGenerator()
                self.character_mapper = CharacterVoiceMapper(self.config_manager.get_config_dir())
            except Exception as e:
                print(f"Warning: Phase 2 features not available: {e}")
        
        if PHASE3_AVAILABLE:
            try:
                self.dialogue_detector = DialogueDetector()
                self.chapter_manager = ChapterManager()
                self.audio_processor = get_audio_processor()
                self.voice_previewer = get_voice_previewer()
            except Exception as e:
                print(f"Warning: Phase 3 features not available: {e}")
        
        # Ensure directories exist
        self.config_manager.get_text_dir().mkdir(exist_ok=True)
        self.config_manager.get_audio_dir().mkdir(exist_ok=True)
        self.config_manager.get_config_dir().mkdir(exist_ok=True)
    
    def get_tts_engine(self):
        """Get TTS engine, initializing if needed."""
        if self.tts_engine is None:
            self.tts_engine = self._initialize_tts_engine()
        return self.tts_engine
    
    def _initialize_tts_engine(self):
        """Initialize TTS engine based on configuration."""
        tts_config = self.config_manager.get_tts_config()
        
        if tts_config.engine == "kokoro" and KOKORO_AVAILABLE:
            try:
                return KokoroEngine()
            except Exception as e:
                # Only show the warning once and update config to prevent repeated attempts
                if "Kokoro models not found" in str(e):
                    print("Info: Kokoro models not yet downloaded. Using pyttsx3 for now.")
                    print("Kokoro models will download automatically on first successful use.")
                else:
                    print(f"Warning: Could not initialize Kokoro engine: {e}")
                # Automatically switch to pyttsx3 to prevent repeated warnings
                self.config_manager.update_tts_config(engine="pyttsx3")
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
        character_voices: Optional[bool] = None,
        chapter_detection: Optional[bool] = None,
        dialogue_detection: Optional[bool] = None
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
        if chapter_detection is not None:
            processing_config.auto_detect_chapters = chapter_detection
        if dialogue_detection is not None:
            processing_config.dialogue_detection = dialogue_detection
        
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
        
        # Create output filename with phase and config info
        audio_dir = self.config_manager.get_audio_dir()
        
        # Build descriptive filename
        phase = processing_config.level
        engine = tts_config.engine
        speed_str = f"speed{tts_config.speed}".replace(".", "p")
        
        # Add feature flags
        features = []
        if processing_config.emotion_analysis:
            features.append("emotion")
        if processing_config.character_voices:
            features.append("characters")
        if processing_config.dialogue_detection:
            features.append("dialogue")
        
        feature_str = "_".join(features) if features else "basic"
        
        output_filename = f"{parsed_content.title}_{phase}_{engine}_{speed_str}_{feature_str}.{audio_config.format}"
        output_path = audio_dir / output_filename
        
        # Phase 1: Simple concatenation for multiple segments
        if len(audio_segments) == 1:
            self.get_tts_engine().save_audio(audio_segments[0], output_path, audio_config.format)
        else:
            # For Phase 1, save each segment as separate file
            click.echo("Phase 1: Saving audio segments as separate files...")
            for i, segment in enumerate(audio_segments):
                segment_path = audio_dir / f"{parsed_content.title}_part_{i+1:03d}.wav"
                self.get_tts_engine().save_audio(segment, segment_path, "wav")
            
            # Save first segment as main file for now
            output_path = output_path.with_suffix('.wav')
            self.get_tts_engine().save_audio(audio_segments[0], output_path, "wav")
        
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
                    tts_engine = self.get_tts_engine()
                    if hasattr(tts_engine, 'supports_ssml') and tts_engine.supports_ssml():
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
                    audio_data = self.get_tts_engine().synthesize(
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
                    audio_data = self.get_tts_engine().synthesize(
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
@click.option('--format', '-f', type=click.Choice(['wav', 'mp3', 'm4a', 'm4b']), help='Output audio format')
@click.option('--file', '-F', type=click.Path(exists=True), help='Convert specific file instead of scanning text/ folder')
@click.option('--engine', '-e', type=click.Choice(['pyttsx3', 'kokoro']), help='TTS engine to use')
@click.option('--emotion/--no-emotion', default=None, help='Enable/disable emotion analysis')
@click.option('--characters/--no-characters', default=None, help='Enable/disable character voice mapping')
@click.option('--chapters/--no-chapters', default=None, help='Enable/disable chapter detection and metadata')
@click.option('--dialogue/--no-dialogue', default=None, help='Enable/disable dialogue detection (Phase 3)')
@click.option('--processing-level', type=click.Choice(['phase1', 'phase2', 'phase3']), help='Set processing level')
def convert(voice, speed, format, file, engine, emotion, characters, chapters, dialogue, processing_level):
    """Convert text files in text/ folder to audiobooks."""
    app = ReaderApp()
    
    # Override processing level if specified
    if processing_level:
        app.config_manager.set_processing_level(processing_level)
        app.tts_engine = app._initialize_tts_engine()
    
    # Override engine if specified
    if engine:
        app.config_manager.update_tts_config(engine=engine)
        app.tts_engine = app._initialize_tts_engine()
    
    if file:
        # Convert specific file
        file_path = Path(file)
        try:
            output_path = app.convert_file(
                file_path, voice, speed, format, emotion, characters, chapters, dialogue
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
                    file_path, voice, speed, format, emotion, characters, chapters, dialogue
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
        engines_to_show.append(('pyttsx3', PyTTSX3Engine()))
        if KOKORO_AVAILABLE:
            # Use static voice list without initializing the engine
            engines_to_show.append(('kokoro', 'static'))
    elif engine == 'kokoro' and KOKORO_AVAILABLE:
        # Use static voice list without initializing the engine
        engines_to_show.append(('kokoro', 'static'))
    elif engine == 'pyttsx3':
        engines_to_show.append(('pyttsx3', PyTTSX3Engine()))
    
    for engine_name, engine_obj in engines_to_show:
        click.echo(f"\n{engine_name.upper()} Voices:")
        click.echo("=" * (len(engine_name) + 8))
        
        if engine_name == 'kokoro' and engine_obj == 'static':
            # Use static Kokoro voice list without full engine initialization
            kokoro_voices = {
                "af_sarah": {"name": "Sarah (American)", "lang": "en-us", "gender": "female"},
                "af_nicole": {"name": "Nicole (American)", "lang": "en-us", "gender": "female"},
                "af_michael": {"name": "Michael (American)", "lang": "en-us", "gender": "male"},
                "af_adam": {"name": "Adam (American)", "lang": "en-us", "gender": "male"},
                "bf_emma": {"name": "Emma (British)", "lang": "en-uk", "gender": "female"},
                "bf_isabella": {"name": "Isabella (British)", "lang": "en-uk", "gender": "female"},
                "bf_oliver": {"name": "Oliver (British)", "lang": "en-uk", "gender": "male"},
                "bf_william": {"name": "William (British)", "lang": "en-uk", "gender": "male"},
                "ef_clara": {"name": "Clara (Spanish)", "lang": "es", "gender": "female"},
                "ef_pedro": {"name": "Pedro (Spanish)", "lang": "es", "gender": "male"},
                "ff_marie": {"name": "Marie (French)", "lang": "fr", "gender": "female"},
                "ff_pierre": {"name": "Pierre (French)", "lang": "fr", "gender": "male"},
            }
            
            available_voices = list(kokoro_voices.keys())
            filtered_voices = available_voices
            
            # Apply filters
            if language:
                filtered_voices = [v for v in available_voices 
                                 if kokoro_voices.get(v, {}).get('lang') == language]
            if gender:
                if language:
                    filtered_voices = [v for v in filtered_voices 
                                     if kokoro_voices.get(v, {}).get('gender') == gender.lower()]
                else:
                    filtered_voices = [v for v in available_voices 
                                     if kokoro_voices.get(v, {}).get('gender') == gender.lower()]
            
            for voice in filtered_voices:
                voice_info = kokoro_voices.get(voice, {})
                click.echo(f"  - {voice}")
                click.echo(f"    Name: {voice_info.get('name', 'unknown')}")
                click.echo(f"    Gender: {voice_info.get('gender', 'unknown')}")
                click.echo(f"    Language: {voice_info.get('lang', 'unknown')}")
        else:
            # Regular engine
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
@click.option('--format', type=click.Choice(['wav', 'mp3', 'm4a', 'm4b']), help='Set default audio format')
@click.option('--engine', type=click.Choice(['pyttsx3', 'kokoro']), help='Set default TTS engine')
@click.option('--emotion/--no-emotion', help='Enable/disable emotion analysis by default')
@click.option('--characters/--no-characters', help='Enable/disable character voices by default')
@click.option('--processing-level', type=click.Choice(['phase1', 'phase2', 'phase3']), help='Set default processing level')
def config(voice, speed, format, engine, emotion, characters, processing_level):
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
    
    # Processing level update
    if processing_level:
        app.config_manager.set_processing_level(processing_level)
        click.echo(f"Processing level set to {processing_level}.")
    
    # Processing configuration updates
    processing_updates = {}
    if emotion is not None:
        processing_updates['emotion_analysis'] = emotion
    if characters is not None:
        processing_updates['character_voices'] = characters
    
    if processing_updates:
        app.config_manager.update_processing_config(**processing_updates)
        click.echo("Processing configuration updated.")
    
    if not any([voice, speed, format, engine, emotion is not None, characters is not None, processing_level]):
        # Display current config
        tts_config = app.config_manager.get_tts_config()
        audio_config = app.config_manager.get_audio_config()
        processing_config = app.config_manager.get_processing_config()
        
        click.echo("Current configuration:")
        click.echo(f"  Processing level: {processing_config.level}")
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
        
        # Phase 3 settings
        if PHASE3_AVAILABLE:
            click.echo("  Phase 3 Features:")
            click.echo(f"    Dialogue detection: {processing_config.dialogue_detection}")
            click.echo(f"    Advanced audio formats: {processing_config.advanced_audio_formats}")
            click.echo(f"    Chapter metadata: {processing_config.chapter_metadata}")


@cli.command()
def info():
    """Show application information and quick start guide."""
    app = ReaderApp()
    
    text_dir = app.config_manager.get_text_dir()
    audio_dir = app.config_manager.get_audio_dir()
    
    # Header
    if PHASE3_AVAILABLE:
        phase = "Phase 3"
    elif PHASE2_AVAILABLE:
        phase = "Phase 2"
    else:
        phase = "Phase 1"
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
    
    if PHASE3_AVAILABLE:
        click.echo("\n🚀 Phase 3 Commands:")
        click.echo("  reader preview VOICE        # Preview voice samples")
        click.echo("  reader chapters extract FILE # Extract chapter structure")
        click.echo("  reader batch add FILES      # Add files to batch queue")
        click.echo("  reader batch process        # Process batch queue")
        click.echo("  reader config --processing-level phase3 # Enable all features")
    
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
    
    if PHASE3_AVAILABLE:
        click.echo("\n🎯 Phase 3 Features:")
        click.echo("  ✅ Professional audio formats (MP3, M4A, M4B)")
        click.echo("  ✅ Advanced dialogue detection with NLP")
        click.echo("  ✅ Chapter extraction and metadata")
        click.echo("  ✅ Voice preview and comparison")
        click.echo("  ✅ Batch processing with progress tracking")
        click.echo("  ✅ Audio normalization and enhancement")
        click.echo("  ✅ Configurable processing levels")
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
        click.echo("  Phase 3: Professional audiobook production")
        click.echo("  Install: poetry add spacy pydub mutagen")
    
    # Tips
    if len(text_files) == 0:
        click.echo("\n💡 Tip: Add text files to get started!")
        click.echo("  echo 'Hello world!' > text/hello.txt")
        click.echo("  poetry run reader convert")
    elif len(audio_files) == 0:
        click.echo("\n💡 Tip: Run 'reader convert' to create audiobooks!")
    else:
        click.echo("\n🎉 Great! You have text and audio files ready.")


# Phase 3 commands
@cli.command()
@click.argument('voice')
@click.option('--engine', type=click.Choice(['pyttsx3', 'kokoro']), default='kokoro', help='TTS engine to use')
@click.option('--text', help='Custom preview text')
@click.option('--emotion', type=click.Choice(['neutral', 'excited', 'sad', 'angry', 'whisper', 'dramatic']), 
              default='neutral', help='Emotional style for preview')
@click.option('--output-dir', type=click.Path(), help='Directory to save preview files')
def preview(voice, engine, text, emotion, output_dir):
    """Generate voice preview samples."""
    if not PHASE3_AVAILABLE:
        click.echo("Voice preview requires Phase 3 dependencies.")
        click.echo("Install with: poetry add spacy pydub mutagen")
        return
    
    app = ReaderApp(init_tts=False)  # TTS initialized by voice_previewer
    if not app.voice_previewer:
        click.echo("Voice previewer not available.")
        return
    
    try:
        output_path = Path(output_dir) if output_dir else None
        preview_file = app.voice_previewer.generate_voice_preview(
            engine_name=engine,
            voice=voice,
            preview_text=text,
            emotion=emotion,
            output_dir=output_path
        )
        
        click.echo(f"✓ Voice preview generated: {preview_file}")
        click.echo("Play the file to hear how this voice sounds.")
        
    except Exception as e:
        click.echo(f"✗ Error generating preview: {e}", err=True)


@cli.group()
def chapters():
    """Manage chapter extraction and metadata."""
    pass


@chapters.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for chapter metadata')
@click.option('--format', type=click.Choice(['json', 'text']), default='json', help='Output format')
def extract(file_path, output, format):
    """Extract chapter structure from a book file."""
    if not PHASE3_AVAILABLE:
        click.echo("Chapter extraction requires Phase 3 dependencies.")
        return
    
    app = ReaderApp(init_tts=False)  # No TTS needed for chapter extraction
    if not app.chapter_manager:
        click.echo("Chapter manager not available.")
        return
    
    input_file = Path(file_path)
    
    try:
        # Extract chapters based on file type
        if input_file.suffix.lower() == '.epub':
            chapters = app.chapter_manager.extract_chapters_from_epub(input_file)
        elif input_file.suffix.lower() == '.pdf':
            chapters = app.chapter_manager.extract_chapters_from_pdf(input_file)
        else:
            # Read as text and extract
            with open(input_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
            chapters = app.chapter_manager.extract_chapters_from_text(text_content)
        
        if not chapters:
            click.echo("No chapters found in the file.")
            return
        
        click.echo(f"Found {len(chapters)} chapters:")
        for i, chapter in enumerate(chapters, 1):
            duration_str = f"{chapter.duration:.1f}s" if chapter.duration else "N/A"
            click.echo(f"  {i}. {chapter.title} ({chapter.word_count} words, ~{duration_str})")
        
        # Save to output file if specified
        if output:
            output_path = Path(output)
            if format == 'json':
                app.chapter_manager.save_chapters_metadata(chapters, output_path)
            else:
                # Save as text report
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"Chapter Structure for: {input_file.name}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    stats = app.chapter_manager.get_chapter_statistics(chapters)
                    f.write(f"Total chapters: {stats['total_chapters']}\n")
                    f.write(f"Total duration: {stats['total_duration_formatted']}\n")
                    f.write(f"Total words: {stats['total_words']}\n\n")
                    
                    for i, chapter in enumerate(chapters, 1):
                        f.write(f"Chapter {i}: {chapter.title}\n")
                        f.write(f"  Words: {chapter.word_count}\n")
                        if chapter.duration:
                            f.write(f"  Duration: {chapter.duration:.1f}s\n")
                        f.write(f"  Start time: {chapter.start_time:.1f}s\n\n")
            
            click.echo(f"✓ Chapter metadata saved to: {output_path}")
        
    except Exception as e:
        click.echo(f"✗ Error extracting chapters: {e}", err=True)


@cli.group()
def batch():
    """Manage batch processing of multiple files."""
    pass


@batch.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--directory', '-d', type=click.Path(exists=True), help='Add all files from directory')
@click.option('--recursive', '-r', is_flag=True, help='Search directory recursively')
@click.option('--output-dir', type=click.Path(), help='Output directory for converted files')
def add(files, directory, recursive, output_dir):
    """Add files to batch processing queue."""
    if not PHASE3_AVAILABLE:
        click.echo("Batch processing requires Phase 3 dependencies.")
        return
    
    app = ReaderApp(init_tts=False)  # Batch processor handles TTS internally
    batch_processor = create_batch_processor(app.config_manager)
    
    job_ids = []
    
    # Add individual files
    for file_path in files:
        input_file = Path(file_path)
        output_file = None
        if output_dir:
            output_file = Path(output_dir) / input_file.with_suffix('.wav').name
        
        job_id = batch_processor.add_job(input_file, output_file)
        job_ids.append(job_id)
        click.echo(f"✓ Added: {input_file.name} (Job ID: {job_id})")
    
    # Add directory
    if directory:
        dir_job_ids = batch_processor.add_directory(
            Path(directory),
            Path(output_dir) if output_dir else None,
            recursive=recursive
        )
        job_ids.extend(dir_job_ids)
        click.echo(f"✓ Added {len(dir_job_ids)} files from directory")
    
    if job_ids:
        click.echo(f"Total jobs in queue: {len(batch_processor.jobs)}")
    else:
        click.echo("No files added to batch queue.")


@batch.command()
@click.option('--max-workers', type=int, default=2, help='Maximum number of concurrent workers')
@click.option('--save-progress', is_flag=True, help='Save progress to file')
def process(max_workers, save_progress):
    """Process all jobs in the batch queue."""
    if not PHASE3_AVAILABLE:
        click.echo("Batch processing requires Phase 3 dependencies.")
        return
    
    app = ReaderApp()
    batch_processor = create_batch_processor(app.config_manager, max_workers)
    
    if not batch_processor.jobs:
        click.echo("No jobs in batch queue. Use 'reader batch add' to add files.")
        return
    
    def progress_callback(job):
        status_symbol = "✓" if job.status.value == "completed" else "✗" if job.status.value == "failed" else "⏳"
        click.echo(f"{status_symbol} {job.input_file.name} - {job.status.value}")
    
    batch_processor.set_progress_callback(progress_callback)
    
    click.echo(f"Processing {len(batch_processor.jobs)} jobs with {max_workers} workers...")
    
    try:
        result = batch_processor.process_batch(save_progress=save_progress)
        
        click.echo(f"\nBatch processing complete!")
        click.echo(f"  Total jobs: {result.total_jobs}")
        click.echo(f"  Completed: {result.completed_jobs}")
        click.echo(f"  Failed: {result.failed_jobs}")
        click.echo(f"  Success rate: {result.success_rate:.1f}%")
        click.echo(f"  Total time: {result.total_duration:.1f}s")
        
        if result.failed_jobs > 0:
            click.echo("\nFailed jobs:")
            for job in result.results:
                if job.status.value == "failed":
                    click.echo(f"  ✗ {job.input_file.name}: {job.error_message}")
    
    except KeyboardInterrupt:
        click.echo("\nBatch processing cancelled by user.")
        batch_processor.cancel_batch()
    except Exception as e:
        click.echo(f"✗ Batch processing error: {e}", err=True)


@batch.command()
def status():
    """Show current batch queue status."""
    if not PHASE3_AVAILABLE:
        click.echo("Batch processing requires Phase 3 dependencies.")
        return
    
    app = ReaderApp()
    batch_processor = create_batch_processor(app.config_manager)
    
    summary = batch_processor.get_batch_summary()
    
    click.echo("Batch Queue Status:")
    click.echo(f"  Total jobs: {summary['total_jobs']}")
    click.echo(f"  Running: {summary['is_running']}")
    
    if summary['total_jobs'] > 0:
        click.echo("  Job status breakdown:")
        for status, count in summary['status_counts'].items():
            if count > 0:
                click.echo(f"    {status}: {count}")


@batch.command()
def clear():
    """Clear all jobs from the batch queue."""
    if not PHASE3_AVAILABLE:
        click.echo("Batch processing requires Phase 3 dependencies.")
        return
    
    app = ReaderApp()
    batch_processor = create_batch_processor(app.config_manager)
    
    if batch_processor.is_running:
        click.echo("Cannot clear queue while batch is running.")
        return
    
    job_count = len(batch_processor.jobs)
    batch_processor.clear_jobs()
    click.echo(f"✓ Cleared {job_count} jobs from batch queue.")


if __name__ == "__main__":
    cli()