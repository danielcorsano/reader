"""Voice preview functionality for Phase 3."""
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import random
import json

from ..interfaces.tts_engine import TTSEngine

try:
    from ..engines.kokoro_engine import KokoroEngine
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False


class VoicePreviewGenerator:
    """Generates voice previews for testing and selection."""
    
    # Sample texts for voice preview
    PREVIEW_TEXTS = [
        "Hello, I'm your audiobook narrator. This is a preview of how I sound when reading your stories.",
        "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet.",
        "In the beginning was the Word, and the Word was with God, and the Word was God.",
        "It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness.",
        "Call me Ishmael. Some years ago—never mind how long precisely—having little or no money in my purse.",
        "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
        "All happy families are alike; each unhappy family is unhappy in its own way.",
        "Once upon a time, in a galaxy far, far away, there lived a princess who needed to be rescued."
    ]
    
    # Emotional preview texts
    EMOTIONAL_PREVIEWS = {
        'neutral': "This is a calm and neutral reading style, perfect for most narrative text.",
        'excited': "Wow! This is an excited and energetic voice that's great for adventure stories!",
        'sad': "This is a melancholy tone, suitable for dramatic or sorrowful passages.",
        'angry': "This voice conveys anger and intensity, perfect for conflict scenes!",
        'whisper': "This is a soft, whispered voice for intimate or mysterious moments.",
        'dramatic': "This is a dramatic reading style with emphasis and theatrical flair!"
    }
    
    def __init__(self):
        """Initialize the voice preview generator."""
        self.engines = {}
        # Don't initialize engines until needed
    
    def _get_engine(self, engine_name: str):
        """Get or initialize an engine on demand."""
        if engine_name not in self.engines:
            if engine_name == 'kokoro' and KOKORO_AVAILABLE:
                try:
                    self.engines[engine_name] = KokoroEngine()
                except Exception as e:
                    raise RuntimeError(f"Could not initialize Kokoro engine: {e}")
            else:
                raise ValueError(f"❌ Only kokoro engine supported. Limited storage? Try reader-small package.")

        return self.engines[engine_name]
    
    def generate_voice_preview(
        self,
        engine_name: str,
        voice: str,
        preview_text: Optional[str] = None,
        emotion: str = 'neutral',
        speed: float = 1.0,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Generate a voice preview audio file.
        
        Args:
            engine_name: Name of TTS engine to use
            voice: Voice identifier
            preview_text: Custom text to use (if None, uses random sample)
            emotion: Emotion style for preview
            speed: Speech speed multiplier
            output_dir: Directory to save preview (if None, uses temp dir)
            
        Returns:
            Path to generated preview audio file
        """
        engine = self._get_engine(engine_name)
        
        # Select preview text
        if preview_text is None:
            if emotion in self.EMOTIONAL_PREVIEWS:
                preview_text = self.EMOTIONAL_PREVIEWS[emotion]
            else:
                preview_text = random.choice(self.PREVIEW_TEXTS)
        
        # Generate audio
        try:
            audio_data = engine.synthesize(
                text=preview_text,
                voice=voice,
                speed=speed,
                volume=1.0
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate preview with {engine_name}: {e}")
        
        # Save to file
        if output_dir is None:
            output_dir = Path(tempfile.gettempdir()) / "reader_previews"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        preview_file = output_dir / f"preview_{engine_name}_{voice}_{emotion}.wav"
        
        engine.save_audio(audio_data, preview_file, "wav")
        
        return preview_file
    
    def generate_voice_comparison(
        self,
        voices: List[str],
        engine_name: str = 'kokoro',
        preview_text: Optional[str] = None,
        output_dir: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate preview files for multiple voices for comparison.
        
        Args:
            voices: List of voice identifiers to compare
            engine_name: TTS engine to use
            preview_text: Text to use for all previews
            output_dir: Output directory for preview files
            
        Returns:
            List of dictionaries with voice info and preview file paths
        """
        if preview_text is None:
            preview_text = "This is a voice comparison preview. Listen carefully to choose your preferred narrator."
        
        results = []
        
        for voice in voices:
            try:
                preview_file = self.generate_voice_preview(
                    engine_name=engine_name,
                    voice=voice,
                    preview_text=preview_text,
                    output_dir=output_dir
                )
                
                # Get voice information
                engine = self._get_engine(engine_name)
                voice_info = engine.get_voice_info(voice)
                
                result = {
                    'voice': voice,
                    'preview_file': str(preview_file),
                    'voice_info': voice_info,
                    'engine': engine_name
                }
                results.append(result)
                
            except Exception as e:
                print(f"Warning: Failed to generate preview for voice '{voice}': {e}")
                results.append({
                    'voice': voice,
                    'error': str(e),
                    'engine': engine_name
                })
        
        return results
    
    def generate_emotional_showcase(
        self,
        voice: str,
        engine_name: str = 'kokoro',
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate emotional range showcase for a single voice.
        
        Args:
            voice: Voice identifier
            engine_name: TTS engine to use
            output_dir: Output directory for preview files
            
        Returns:
            Dictionary with emotional preview file paths
        """
        results = {
            'voice': voice,
            'engine': engine_name,
            'emotional_previews': {}
        }
        
        for emotion, text in self.EMOTIONAL_PREVIEWS.items():
            try:
                preview_file = self.generate_voice_preview(
                    engine_name=engine_name,
                    voice=voice,
                    preview_text=text,
                    emotion=emotion,
                    output_dir=output_dir
                )
                
                results['emotional_previews'][emotion] = str(preview_file)
                
            except Exception as e:
                print(f"Warning: Failed to generate {emotion} preview for '{voice}': {e}")
                results['emotional_previews'][emotion] = f"Error: {e}"
        
        return results
    
    def create_preview_playlist(
        self,
        preview_results: List[Dict[str, Any]],
        output_file: Path
    ) -> None:
        """
        Create a playlist file for easy preview playback.
        
        Args:
            preview_results: Results from voice comparison or emotional showcase
            output_file: Path for output playlist file
        """
        playlist_data = {
            'title': 'Voice Preview Playlist',
            'created_by': 'Reader Voice Previewer',
            'previews': preview_results
        }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if output_file.suffix.lower() == '.json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
        
        elif output_file.suffix.lower() == '.m3u':
            # Create M3U playlist for audio players
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                f.write("# Voice Preview Playlist\n")
                
                for result in preview_results:
                    if 'preview_file' in result:
                        voice_name = result.get('voice', 'Unknown')
                        f.write(f"#EXTINF:-1,{voice_name}\n")
                        f.write(f"{result['preview_file']}\n")
        
        else:
            # Default to JSON
            with open(output_file.with_suffix('.json'), 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
    
    def get_recommended_voices(
        self,
        engine_name: str,
        genre: str = 'general',
        gender_preference: Optional[str] = None
    ) -> List[str]:
        """
        Get recommended voices based on criteria.
        
        Args:
            engine_name: TTS engine name
            genre: Book genre ('general', 'fiction', 'nonfiction', 'children', 'romance', 'thriller')
            gender_preference: Preferred gender ('male', 'female', None for any)
            
        Returns:
            List of recommended voice identifiers
        """
        try:
            engine = self._get_engine(engine_name)
        except:
            return []
        available_voices = engine.list_voices()
        
        if engine_name == 'kokoro' and hasattr(engine, 'VOICES'):
            # Use Kokoro's detailed voice information
            recommendations = []
            
            for voice_id, voice_info in engine.VOICES.items():
                # Filter by gender if specified
                if gender_preference and voice_info.get('gender') != gender_preference.lower():
                    continue
                
                # Genre-specific recommendations
                if genre == 'children':
                    # Prefer younger, friendlier voices
                    if 'sarah' in voice_id.lower() or 'emma' in voice_id.lower():
                        recommendations.append(voice_id)
                elif genre == 'thriller':
                    # Prefer dramatic voices
                    if 'michael' in voice_id.lower() or 'william' in voice_id.lower():
                        recommendations.append(voice_id)
                elif genre == 'romance':
                    # Prefer warm, expressive voices
                    if 'nicole' in voice_id.lower() or 'isabella' in voice_id.lower():
                        recommendations.append(voice_id)
                else:
                    # General recommendations
                    recommendations.append(voice_id)
            
            return recommendations[:6]  # Limit to top 6 recommendations
        
        else:
            # For other engines (if any added later), return available voices
            return available_voices[:6] if available_voices else []
    
    def analyze_voice_characteristics(
        self,
        voice: str,
        engine_name: str,
        sample_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze voice characteristics (placeholder for future ML analysis).
        
        Args:
            voice: Voice identifier
            engine_name: TTS engine name
            sample_text: Text to analyze (if None, uses default)
            
        Returns:
            Dictionary with voice characteristics
        """
        try:
            engine = self._get_engine(engine_name)
        except Exception as e:
            return {'error': f'Engine {engine_name} not available: {e}'}
        voice_info = engine.get_voice_info(voice)
        
        # Basic characteristics from engine info
        characteristics = {
            'voice': voice,
            'engine': engine_name,
            'basic_info': voice_info,
            'estimated_characteristics': {}
        }
        
        # Estimate characteristics based on voice name/info
        if engine_name == 'kokoro' and hasattr(engine, 'VOICES'):
            kokoro_info = engine.VOICES.get(voice, {})
            characteristics['estimated_characteristics'] = {
                'language': kokoro_info.get('lang', 'unknown'),
                'gender': kokoro_info.get('gender', 'unknown'),
                'accent': 'American' if 'af_' in voice else 'British' if 'bf_' in voice else 'Other',
                'suitability': self._estimate_voice_suitability(voice, kokoro_info)
            }
        
        # TODO: In the future, this could include:
        # - Pitch analysis
        # - Speed analysis  
        # - Emotional range detection
        # - Clarity/articulation scoring
        # - Background noise levels
        
        return characteristics
    
    def _estimate_voice_suitability(self, voice_id: str, voice_info: Dict[str, Any]) -> List[str]:
        """Estimate what types of content a voice is suitable for."""
        suitability = []
        
        gender = voice_info.get('gender', '').lower()
        name = voice_info.get('name', '').lower()
        
        # General suitability
        suitability.append('general')
        
        # Gender-based
        if gender == 'female':
            suitability.extend(['romance', 'young_adult', 'memoir'])
        elif gender == 'male':
            suitability.extend(['thriller', 'biography', 'business'])
        
        # Name-based heuristics
        if any(x in name for x in ['sarah', 'emma', 'clara']):
            suitability.extend(['children', 'fantasy', 'light_fiction'])
        elif any(x in name for x in ['michael', 'william', 'oliver']):
            suitability.extend(['non_fiction', 'history', 'business'])
        elif any(x in name for x in ['nicole', 'isabella']):
            suitability.extend(['drama', 'romance', 'literary_fiction'])
        
        return list(set(suitability))  # Remove duplicates
    
    def cleanup_previews(self, preview_dir: Path, older_than_hours: int = 24) -> int:
        """
        Clean up old preview files.
        
        Args:
            preview_dir: Directory containing preview files
            older_than_hours: Remove files older than this many hours
            
        Returns:
            Number of files removed
        """
        import time
        
        if not preview_dir.exists():
            return 0
        
        cutoff_time = time.time() - (older_than_hours * 3600)
        removed_count = 0
        
        for file_path in preview_dir.glob("preview_*.wav"):
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    removed_count += 1
            except Exception:
                pass  # Ignore errors during cleanup
        
        return removed_count


class VoiceSelector:
    """Helper class for interactive voice selection."""
    
    def __init__(self, preview_generator: VoicePreviewGenerator):
        """Initialize with a preview generator."""
        self.preview_generator = preview_generator
    
    def interactive_voice_selection(
        self,
        engine_name: str,
        max_options: int = 5,
        genre: str = 'general'
    ) -> Optional[str]:
        """
        Interactive voice selection process (for CLI use).
        
        Args:
            engine_name: TTS engine to use
            max_options: Maximum number of voice options to present
            genre: Genre for voice recommendations
            
        Returns:
            Selected voice identifier or None if cancelled
        """
        # Get recommended voices
        recommended = self.preview_generator.get_recommended_voices(
            engine_name=engine_name,
            genre=genre
        )
        
        if not recommended:
            print(f"No voices available for engine '{engine_name}'")
            return None
        
        # Limit options
        options = recommended[:max_options]
        
        print(f"\nAvailable voices for {engine_name}:")
        for i, voice in enumerate(options, 1):
            print(f"{i}. {voice}")
        
        print(f"{len(options) + 1}. Generate previews for comparison")
        print(f"{len(options) + 2}. Cancel")
        
        try:
            choice = input("\nSelect a voice (enter number): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(options):
                return options[choice_num - 1]
            elif choice_num == len(options) + 1:
                # Generate previews
                self._generate_comparison_previews(engine_name, options)
                return self.interactive_voice_selection(engine_name, max_options, genre)
            else:
                return None
                
        except (ValueError, KeyboardInterrupt):
            return None
    
    def _generate_comparison_previews(self, engine_name: str, voices: List[str]) -> None:
        """Generate and announce preview files for comparison."""
        print(f"\nGenerating voice previews for comparison...")
        
        try:
            results = self.preview_generator.generate_voice_comparison(
                voices=voices,
                engine_name=engine_name
            )
            
            print("\nGenerated preview files:")
            for result in results:
                if 'preview_file' in result:
                    print(f"  {result['voice']}: {result['preview_file']}")
                else:
                    print(f"  {result['voice']}: Error - {result.get('error', 'Unknown error')}")
            
            print("\nListen to the preview files and run the command again to make your selection.")
            
        except Exception as e:
            print(f"Error generating previews: {e}")


def get_voice_previewer() -> VoicePreviewGenerator:
    """Get a voice preview generator instance."""
    return VoicePreviewGenerator()