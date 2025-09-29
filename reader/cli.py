"""Main CLI interface for the reader application."""
import click
from pathlib import Path
from typing import List, Optional
import sys
import warnings

# Suppress known warnings from dependencies
warnings.filterwarnings("ignore", 
                       message=".*This search incorrectly ignores the root element.*",
                       category=FutureWarning,
                       module="ebooklib.*")

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
    from .batch.neural_processor import NeuralProcessor
    from .processors.ffmpeg_processor import get_audio_processor
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
    
    def _apply_temporary_overrides(self, overrides: dict):
        """Apply temporary CLI parameter overrides without saving to config file."""
        # Apply processing level override
        if 'processing_level' in overrides:
            level = overrides['processing_level']
            # Temporarily modify the config objects in memory
            config = self.config_manager.config
            config.processing.level = level
            
            # Auto-configure features based on level (in memory only)
            if level == "phase1":
                config.processing.emotion_analysis = False
                config.processing.character_voices = False
                config.processing.dialogue_detection = False
                config.processing.advanced_audio_formats = False
            elif level == "phase2":
                config.processing.emotion_analysis = True
                config.processing.character_voices = True
                config.processing.dialogue_detection = False
                config.processing.advanced_audio_formats = False
            elif level == "phase3":
                config.processing.emotion_analysis = True
                config.processing.character_voices = True
                config.processing.dialogue_detection = True
                config.processing.advanced_audio_formats = True
        
        # Apply engine override
        if 'engine' in overrides:
            engine = overrides['engine']
            # Temporarily modify the config object in memory
            self.config_manager.config.tts.engine = engine
        
        # Reinitialize TTS engine if needed
        if 'engine' in overrides:
            self.tts_engine = self._initialize_tts_engine()
    
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
        dialogue_detection: Optional[bool] = None,
        batch_mode: bool = False,
        checkpoint_interval: int = 50,
        turbo_mode: bool = False,
        debug: bool = False
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
        
        if debug:
            print(f"🔍 DEBUG: Loaded config values:")
            print(f"   TTS: engine={tts_config.engine}, voice={tts_config.voice}, speed={tts_config.speed}")
            print(f"   Audio: format={audio_config.format}")
            print(f"   Processing: level={processing_config.level}, emotion={processing_config.emotion_analysis}, characters={processing_config.character_voices}")
            print(f"   Chunk size: {processing_config.chunk_size}")
        
        # Override with command-line arguments
        if voice:
            if debug: print(f"🔍 DEBUG: Overriding voice: {tts_config.voice} -> {voice}")
            tts_config.voice = voice
        if speed:
            if debug: print(f"🔍 DEBUG: Overriding speed: {tts_config.speed} -> {speed}")
            tts_config.speed = speed
        if format:
            if debug: print(f"🔍 DEBUG: Overriding format: {audio_config.format} -> {format}")
            audio_config.format = format
        if emotion_analysis is not None:
            if debug: print(f"🔍 DEBUG: Overriding emotion: {processing_config.emotion_analysis} -> {emotion_analysis}")
            processing_config.emotion_analysis = emotion_analysis
        if character_voices is not None:
            if debug: print(f"🔍 DEBUG: Overriding characters: {processing_config.character_voices} -> {character_voices}")
            processing_config.character_voices = character_voices
        if chapter_detection is not None:
            if debug: print(f"🔍 DEBUG: Overriding chapters: {processing_config.auto_detect_chapters} -> {chapter_detection}")
            processing_config.auto_detect_chapters = chapter_detection
        if dialogue_detection is not None:
            if debug: print(f"🔍 DEBUG: Overriding dialogue: {processing_config.dialogue_detection} -> {dialogue_detection}")
            processing_config.dialogue_detection = dialogue_detection
            
        if debug:
            print(f"🔍 DEBUG: Final config after overrides:")
            print(f"   TTS: engine={tts_config.engine}, voice={tts_config.voice}, speed={tts_config.speed}")
            print(f"   Audio: format={audio_config.format}")
            print(f"   Processing: level={processing_config.level}, emotion={processing_config.emotion_analysis}, characters={processing_config.character_voices}")
        
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
        
        # Use Neural Engine processing for Phase 3 (default)
        if PHASE3_AVAILABLE:
            # Use Neural Engine processing with streaming and checkpoints
            audio_segments = self._convert_with_robust_processing(
                file_path, parsed_content, tts_config, processing_config, 
                checkpoint_interval=25, thermal_management=False, chunk_delay=0.0, 
                parallel=False, max_workers=8
            )
        elif processing_config.emotion_analysis and self.ssml_generator:
            # Fallback: Process with emotion and character awareness
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
        voice = tts_config.voice or "default"
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
        
        output_filename = f"{parsed_content.title}_{phase}_{engine}_{voice}_{speed_str}_{feature_str}.{audio_config.format}"
        output_path = audio_dir / output_filename
        
        # Combine audio segments into final audiobook
        if len(audio_segments) == 0:
            # Neural Engine processor already wrote the file directly
            click.echo("Audio file already written by Neural Engine processor")
        elif len(audio_segments) == 1:
            self.get_tts_engine().save_audio(audio_segments[0], output_path, audio_config.format)
        else:
            # Merge all segments into a single audio file
            click.echo(f"Merging {len(audio_segments)} audio segments...")
            merged_audio = self._merge_audio_segments(audio_segments)
            output_path = output_path.with_suffix(f'.{audio_config.format}')
            self.get_tts_engine().save_audio(merged_audio, output_path, audio_config.format)
        
        # Phase 1: Skip metadata (requires complex audio libraries)
        if audio_config.add_metadata:
            click.echo("Phase 1: Metadata addition will be available in Phase 2+")
        
        click.echo(f"Audiobook saved to: {output_path}")
        return output_path
    
    def _get_expected_output_path(self, file_path: Path, voice=None, speed=None, format=None, 
                                emotion=None, characters=None, chapters=None, dialogue=None, 
                                processing_level=None, turbo_mode=False) -> Path:
        """Get expected output path for a file with given settings."""
        # Get parser and parse just the title
        parser = self.get_parser_for_file(file_path)
        if not parser:
            raise ValueError(f"No parser available for file: {file_path}")
        
        parsed_content = parser.parse(file_path)
        
        # Get configurations with overrides
        tts_config = self.config_manager.get_tts_config()
        audio_config = self.config_manager.get_audio_config()
        processing_config = self.config_manager.get_processing_config()
        
        # Apply overrides
        if voice:
            tts_config.voice = voice
        if speed:
            tts_config.speed = speed
        if format:
            audio_config.format = format
        if emotion is not None:
            processing_config.emotion_analysis = emotion
        if characters is not None:
            processing_config.character_voices = characters
        if chapters is not None:
            processing_config.auto_detect_chapters = chapters
        if dialogue is not None:
            processing_config.dialogue_detection = dialogue
        if processing_level:
            processing_config.level = processing_level
        
        # Generate the same output path that would be created
        return self._create_output_path(parsed_content.title, tts_config, audio_config, processing_config)
    
    def _convert_with_emotion_analysis(self, parsed_content, tts_config, processing_config):
        """Convert content with emotion analysis and smart acting."""
        audio_segments = []
        
        # Split into sentences for better emotion analysis
        sentences = self._split_into_sentences(parsed_content.content)
        
        for sentence in sentences:
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
        
        for chunk in chunks:
            if chunk.strip():
                audio_data = self.get_tts_engine().synthesize(
                    text=chunk,
                    voice=tts_config.voice,
                    speed=tts_config.speed,
                    volume=tts_config.volume
                )
                audio_segments.append(audio_data)
        
        return audio_segments
    
    def _convert_with_robust_processing(self, file_path, parsed_content, tts_config, processing_config, checkpoint_interval, thermal_management, chunk_delay, parallel=False, max_workers=8):
        """Convert using simple streaming processor with checkpoints."""
        if not PHASE3_AVAILABLE:
            raise RuntimeError("Batch processing requires Phase 3 components")
        
        # Create output file path  
        audio_config = self.config_manager.get_audio_config()
        output_path = self._create_output_path(parsed_content.title, tts_config, audio_config, processing_config)
        
        # Create Neural Engine processor with optimized settings
        processor = NeuralProcessor(
            output_path=output_path,
            checkpoint_interval=checkpoint_interval
        )
        
        # Split content into optimized chunks for maximum performance
        if tts_config.engine == "kokoro" and KOKORO_AVAILABLE:
            # Use Kokoro's optimized chunking with much larger chunks
            kokoro_engine = self.get_tts_engine()
            text_chunks = kokoro_engine._chunk_text_intelligently(parsed_content.content, max_length=1200)  # 3x larger for speed
        else:
            # Use basic chunking for other engines
            chunk_size = min(1200, processing_config.chunk_size * 3)  # Much larger chunks for speed
            text_chunks = [parsed_content.content[i:i+chunk_size] 
                          for i in range(0, len(parsed_content.content), chunk_size)]
        
        # Get voice blend configuration
        voice_blend = {}
        if tts_config.voice:
            voice_blend = {tts_config.voice: 1.0}
        else:
            # Default voice
            if tts_config.engine == "kokoro":
                voice_blend = {"am_michael": 1.0}
            else:
                voice_blend = {"default": 1.0}
        
        # Processing configuration for checkpoints
        proc_config = {
            'engine': tts_config.engine,
            'voice': tts_config.voice,
            'speed': tts_config.speed,
            'processing_level': processing_config.level,
            'format': self.config_manager.get_audio_config().format
        }
        
        # Process with Neural Engine optimization
        result_path = processor.process_chunks(
            file_path=file_path,
            text_chunks=text_chunks,
            tts_engine=self.get_tts_engine(),
            voice_blend=voice_blend,
            speed=tts_config.speed,
            processing_config=proc_config
        )
        
        # Return empty list since audio is already written to file
        return []
    
    def _split_into_sentences(self, text):
        """Split text into sentences for emotion analysis."""
        import re
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _merge_audio_segments(self, audio_segments):
        """Merge multiple audio segments into a single audio file."""
        if not audio_segments:
            return b''
        
        if len(audio_segments) == 1:
            return audio_segments[0]
        
        # Merge WAV files properly by concatenating audio data and updating header
        import struct
        
        # Start with the first segment
        merged_audio = bytearray(audio_segments[0])
        
        # Extract audio data from subsequent segments and append
        for segment in audio_segments[1:]:
            if len(segment) > 44:
                # Skip WAV header (44 bytes) and append audio data
                audio_data = segment[44:]
                merged_audio.extend(audio_data)
        
        # Update the WAV header to reflect the new file size
        if len(merged_audio) > 44:
            # Update file size in RIFF header (bytes 4-7)
            file_size = len(merged_audio) - 8
            merged_audio[4:8] = struct.pack('<L', file_size)
            
            # Update data chunk size (bytes 40-43)
            data_size = len(merged_audio) - 44
            merged_audio[40:44] = struct.pack('<L', data_size)
        
        return bytes(merged_audio)
    
    def _create_output_path(self, title, tts_config, audio_config, processing_config):
        """Create standardized output path for audio files."""
        audio_dir = self.config_manager.get_audio_dir()
        
        # Build descriptive filename
        phase = processing_config.level
        engine = tts_config.engine
        voice = tts_config.voice or "default"
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
        
        output_filename = f"{title}_{phase}_{engine}_{voice}_{speed_str}_{feature_str}.{audio_config.format}"
        return audio_dir / output_filename


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
@click.option('--engine', '-e', type=click.Choice(['pyttsx3', 'kokoro']), help='TTS engine to use (temporary override)')
@click.option('--emotion/--no-emotion', default=None, help='Enable/disable emotion analysis (temporary override)')
@click.option('--characters/--no-characters', default=None, help='Enable/disable character voice mapping (temporary override)')
@click.option('--chapters/--no-chapters', default=None, help='Enable/disable chapter detection and metadata (temporary override)')
@click.option('--dialogue/--no-dialogue', default=None, help='Enable/disable dialogue detection (Phase 3, temporary override)')
@click.option('--processing-level', type=click.Choice(['phase1', 'phase2', 'phase3']), help='Set processing level (temporary override)')
@click.option('--batch-mode', is_flag=True, help='Enable robust batch processing with checkpoints')
@click.option('--checkpoint-interval', type=int, default=50, help='Save checkpoint every N chunks (default: 50)')
@click.option('--turbo-mode', is_flag=True, default=False, help='Enable maximum performance mode (minimal delays, 95% CPU)')
@click.option('--debug', is_flag=True, default=False, help='Enable detailed debug output')
def convert(voice, speed, format, file, engine, emotion, characters, chapters, dialogue, processing_level, batch_mode, checkpoint_interval, turbo_mode, debug):
    """Convert text files in text/ folder to audiobooks.
    
    All options are temporary overrides and won't be saved to config.
    Use 'reader config' to permanently save settings."""
    app = ReaderApp()
    
    # Apply temporary overrides without modifying config file
    temp_overrides = {}
    
    if processing_level:
        temp_overrides['processing_level'] = processing_level
    if engine:
        temp_overrides['engine'] = engine
    
    # Apply overrides and reinitialize if needed
    if temp_overrides:
        app._apply_temporary_overrides(temp_overrides)
    
    if file:
        # Convert specific file
        file_path = Path(file)
        # Apply turbo mode settings
        if turbo_mode:
            click.echo("🚀 Turbo mode enabled: Maximum performance settings active")
        
        try:
            if debug:
                click.echo(f"🔍 DEBUG: CLI parameters passed to convert_file:")
                click.echo(f"   voice={voice}, speed={speed}, format={format}")
                click.echo(f"   emotion={emotion}, characters={characters}, chapters={chapters}, dialogue={dialogue}")
                click.echo(f"   batch_mode={batch_mode}, turbo_mode={turbo_mode}")
            
            output_path = app.convert_file(
                file_path, voice, speed, format, emotion, characters, chapters, dialogue,
                batch_mode=batch_mode, checkpoint_interval=checkpoint_interval,
                turbo_mode=turbo_mode, debug=debug
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
        
        # Convert each file (skip if already converted, continue if partial)
        for file_path in text_files:
            # Check if already converted with same settings
            expected_output = app._get_expected_output_path(file_path, voice, speed, format, emotion, characters, chapters, dialogue, processing_level, turbo_mode)
            checkpoint_path = expected_output.with_suffix('.checkpoint')
            
            if expected_output.exists() and not checkpoint_path.exists():
                click.echo(f"⏭️ Skipping {file_path.name} (already converted: {expected_output.name})")
                continue
            elif checkpoint_path.exists():
                click.echo(f"📂 Resuming {file_path.name} from checkpoint...")
                
            try:
                output_path = app.convert_file(
                    file_path, voice, speed, format, emotion, characters, chapters, dialogue,
                    batch_mode=batch_mode, checkpoint_interval=checkpoint_interval,
                    turbo_mode=turbo_mode
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
            engines_to_show.append(('kokoro', 'static'))
    elif engine == 'kokoro' and KOKORO_AVAILABLE:
        engines_to_show.append(('kokoro', 'static'))
    elif engine == 'pyttsx3':
        engines_to_show.append(('pyttsx3', PyTTSX3Engine()))
    
    for engine_name, engine_obj in engines_to_show:
        click.echo(f"\n{engine_name.upper()} Voices:")
        click.echo("=" * (len(engine_name) + 8))
        
        if engine_name == 'kokoro' and engine_obj == 'static':
            # Use KokoroEngine voices (avoid duplication)
            from .engines.kokoro_engine import KokoroEngine
            kokoro_voices = KokoroEngine.VOICES
            
            # Get all available voices (avoid list(keys()) to prevent Click argument parsing issue)
            filtered_voices = [
                voice_id for voice_id in kokoro_voices
            ]
            
            # Apply filters if specified
            if language:
                filtered_voices = [v for v in filtered_voices 
                                 if kokoro_voices[v]['lang'] == language]
            if gender:
                filtered_voices = [v for v in filtered_voices 
                                 if kokoro_voices[v]['gender'] == gender.lower()]
            
            # Display voices
            for voice in filtered_voices:
                voice_info = kokoro_voices[voice]
                click.echo(f"  - {voice}")
                click.echo(f"    Name: {voice_info['name']}")
                click.echo(f"    Gender: {voice_info['gender']}")
                click.echo(f"    Language: {voice_info['lang']}")
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
@click.option('--monitor', is_flag=True, help='Monitor current conversion progress')
def progress(monitor):
    """Monitor conversion progress in real-time."""
    if not PHASE3_AVAILABLE:
        click.echo("Progress monitoring requires Phase 3 components.")
        return
    
    processor = RobustProcessor()
    
    if monitor:
        import time
        try:
            while True:
                summary = processor.get_system_status()
                checkpoints = processor.list_all_checkpoints()
                
                click.clear()
                click.echo("📊 Real-time Progress Monitor")
                click.echo("=" * 40)
                
                if checkpoints:
                    for cp in checkpoints[:3]:  # Show top 3
                        file_name = Path(cp['file']).name
                        click.echo(f"📄 {file_name}")
                        click.echo(f"   Progress: {cp['progress']} ({cp['percent']:.1f}%)")
                        
                        # Progress bar
                        bar_length = 30
                        filled = int(cp['percent'] / 100 * bar_length)
                        bar = "█" * filled + "░" * (bar_length - filled)
                        click.echo(f"   [{bar}] {cp['percent']:.1f}%")
                        click.echo()
                
                click.echo(f"💾 System: {summary['disk_usage_mb']:.1f}MB disk usage")
                click.echo("Press Ctrl+C to stop monitoring")
                
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            click.echo("\n👋 Monitoring stopped.")
    else:
        # One-time status check
        summary = processor.get_system_status()
        checkpoints = processor.list_all_checkpoints()
        
        if checkpoints:
            click.echo("📊 Current Progress:")
            for cp in checkpoints:
                file_name = Path(cp['file']).name
                click.echo(f"📄 {file_name}: {cp['percent']:.1f}% complete")
        else:
            click.echo("No active conversions found.")


@cli.command()
@click.option('--list', 'list_checkpoints', is_flag=True, help='List all checkpoints')
@click.option('--cleanup', type=click.Path(exists=True), help='Clean up checkpoint for specific file')
@click.option('--status', type=click.Path(exists=True), help='Show processing status for specific file')
@click.option('--summary', is_flag=True, help='Show checkpoint system summary')
def checkpoints(list_checkpoints, cleanup, status, summary):
    """Manage batch processing checkpoints."""
    if not PHASE3_AVAILABLE:
        click.echo("Checkpoint management requires Phase 3 components.")
        return
    
    processor = RobustProcessor()
    
    if list_checkpoints:
        checkpoints = processor.list_all_checkpoints()
        if not checkpoints:
            click.echo("No checkpoints found.")
            return
        
        click.echo("📂 Available Checkpoints:")
        for cp in checkpoints:
            age = f"{cp['age_hours']:.1f}h ago" if cp['age_hours'] < 24 else f"{cp['age_hours']/24:.1f}d ago"
            click.echo(f"  📄 {Path(cp['file']).name}")
            click.echo(f"      Progress: {cp['progress']} ({cp['percent']:.1f}%)")
            click.echo(f"      Age: {age}")
            click.echo()
    
    elif cleanup:
        file_path = Path(cleanup)
        if processor.cleanup_checkpoint(file_path):
            click.echo(f"✅ Checkpoint cleaned up for {file_path.name}")
        else:
            click.echo(f"❌ Failed to cleanup checkpoint for {file_path.name}")
    
    elif status:
        file_path = Path(status)
        status_info = processor.get_processing_status(file_path)
        
        if not status_info['has_checkpoint']:
            click.echo(f"📄 {file_path.name}: No checkpoint found")
        else:
            progress = status_info['progress']
            age = f"{status_info['age_hours']:.1f}h ago" if status_info['age_hours'] < 24 else f"{status_info['age_hours']/24:.1f}d ago"
            
            click.echo(f"📄 {file_path.name}")
            click.echo(f"   Status: {status_info['status']}")
            click.echo(f"   Progress: {progress['completed']}/{progress['total']} ({progress['percent']:.1f}%)")
            click.echo(f"   Last update: {age}")
    
    elif summary:
        summary_info = processor.get_system_status()
        click.echo("📊 Checkpoint System Summary:")
        click.echo(f"   Active checkpoints: {summary_info['active_checkpoints']}")
        click.echo(f"   Total segments: {summary_info['total_segments']}")
        click.echo(f"   Disk usage: {summary_info['disk_usage_mb']:.1f} MB")
        click.echo(f"   Checkpoint directory: {summary_info['checkpoint_dir']}")
        
        if summary_info['recent_checkpoints']:
            click.echo("\n📂 Recent Checkpoints:")
            for cp in summary_info['recent_checkpoints']:
                click.echo(f"   📄 {Path(cp['file']).name} ({cp['percent']:.1f}%)")
    
    else:
        click.echo("Use --help to see checkpoint management options.")


@cli.command()
@click.option('--voice', help='Set default voice (saved to config)')
@click.option('--speed', type=float, help='Set default speed (saved to config)')
@click.option('--format', type=click.Choice(['wav', 'mp3', 'm4a', 'm4b']), help='Set default audio format (saved to config)')
@click.option('--engine', type=click.Choice(['pyttsx3', 'kokoro']), help='Set default TTS engine (saved to config)')
@click.option('--emotion/--no-emotion', help='Enable/disable emotion analysis by default (saved to config)')
@click.option('--characters/--no-characters', help='Enable/disable character voices by default (saved to config)')
@click.option('--processing-level', type=click.Choice(['phase1', 'phase2', 'phase3']), help='Set default processing level (saved to config)')
def config(voice, speed, format, engine, emotion, characters, processing_level):
    """Configure default settings (permanently saved to config file)."""
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