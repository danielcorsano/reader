"""Character voice mapping and management system."""
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import re

from ..engines.kokoro_engine import KokoroEngine
from ..analysis.gender_detector import GenderDetector


@dataclass
class CharacterVoice:
    """Configuration for a character's voice."""
    name: str
    voice_id: str  # Kokoro voice ID or blend
    gender: str


@dataclass 
class VoiceBlend:
    """Configuration for a custom voice blend."""
    name: str
    voices: Dict[str, float]  # voice_id -> weight (0.0-1.0)
    description: str


class CharacterVoiceMapper:
    """Manages character-to-voice mappings and voice blending."""
    
    def __init__(self, config_dir: Path):
        """Initialize character voice mapper."""
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)

        self.characters_file = config_dir / "characters.yaml"
        self.voice_blends_file = config_dir / "voice_blends.yaml"

        self.characters: Dict[str, CharacterVoice] = {}
        self.voice_blends: Dict[str, VoiceBlend] = {}
        self.gender_detector = GenderDetector()

        self.load_configurations()
    
    def load_configurations(self) -> None:
        """Load character and voice blend configurations."""
        # Load characters
        if self.characters_file.exists():
            try:
                with open(self.characters_file, 'r') as f:
                    char_data = yaml.safe_load(f) or {}

                # Filter out old fields that no longer exist (backwards compatibility)
                self.characters = {}
                for name, data in char_data.items():
                    # Only keep valid fields
                    filtered_data = {k: v for k, v in data.items() if k in ['name', 'voice_id', 'gender']}
                    self.characters[name] = CharacterVoice(**filtered_data)
            except Exception as e:
                print(f"Warning: Could not load characters config: {e}")
        
        # Load voice blends
        if self.voice_blends_file.exists():
            try:
                with open(self.voice_blends_file, 'r') as f:
                    blend_data = yaml.safe_load(f) or {}
                
                self.voice_blends = {
                    name: VoiceBlend(**data)
                    for name, data in blend_data.items()
                }
            except Exception as e:
                print(f"Warning: Could not load voice blends config: {e}")
    
    def save_configurations(self) -> None:
        """Save character and voice blend configurations."""
        # Save characters
        char_data = {name: asdict(char) for name, char in self.characters.items()}
        with open(self.characters_file, 'w') as f:
            yaml.dump(char_data, f, default_flow_style=False, indent=2)

        # Save voice blends
        blend_data = {name: asdict(blend) for name, blend in self.voice_blends.items()}
        with open(self.voice_blends_file, 'w') as f:
            yaml.dump(blend_data, f, default_flow_style=False, indent=2)

    def load_from_file(self, config_file: Path) -> int:
        """
        Load character voice mappings from an external YAML file.

        Expected format:
        characters:
          - name: Alice
            voice: af_sarah
            gender: female
          - name: Bob
            voice: am_michael
            gender: male

        Returns:
            Number of characters loaded
        """
        if not config_file.exists():
            return 0

        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)

            if not data or 'characters' not in data:
                return 0

            count = 0
            for char_data in data['characters']:
                if 'name' in char_data and 'voice' in char_data:
                    self.add_character(
                        name=char_data['name'],
                        voice_id=char_data['voice'],
                        gender=char_data.get('gender', 'unknown')
                    )
                    count += 1

            return count

        except Exception as e:
            print(f"Warning: Could not load character config from {config_file}: {e}")
            return 0
    
    def add_character(
        self,
        name: str,
        voice_id: str,
        gender: str = "unknown"
    ) -> None:
        """Add or update a character voice mapping."""
        character = CharacterVoice(
            name=name,
            voice_id=voice_id,
            gender=gender
        )

        self.characters[name] = character
        self.save_configurations()
    
    def remove_character(self, name: str) -> bool:
        """Remove a character mapping."""
        if name in self.characters:
            del self.characters[name]
            self.save_configurations()
            return True
        return False
    
    def get_character_voice(self, name: str) -> Optional[CharacterVoice]:
        """Get voice configuration for a character."""
        return self.characters.get(name)
    
    def list_characters(self) -> List[str]:
        """Get list of configured character names."""
        return list(self.characters.keys())
    
    def create_voice_blend(
        self,
        name: str,
        voice_weights: Dict[str, float],
        description: str = ""
    ) -> str:
        """
        Create a custom voice blend.
        
        Args:
            name: Name for the blend
            voice_weights: Dict of voice_id -> weight (0.0-1.0)
            description: Description of the blend
            
        Returns:
            Voice blend specification string for TTS engines
        """
        # Normalize weights to sum to 1.0
        total_weight = sum(voice_weights.values())
        if total_weight > 0:
            normalized_weights = {
                voice: weight / total_weight 
                for voice, weight in voice_weights.items()
            }
        else:
            normalized_weights = voice_weights
        
        # Create blend object
        blend = VoiceBlend(
            name=name,
            voices=normalized_weights,
            description=description
        )
        
        self.voice_blends[name] = blend
        self.save_configurations()
        
        # Return Kokoro-compatible blend string
        return self._blend_to_voice_spec(blend)
    
    def get_voice_blend(self, name: str) -> Optional[VoiceBlend]:
        """Get a voice blend by name."""
        return self.voice_blends.get(name)
    
    def list_voice_blends(self) -> List[str]:
        """Get list of available voice blends."""
        return list(self.voice_blends.keys())
    
    def _blend_to_voice_spec(self, blend: VoiceBlend) -> str:
        """Convert voice blend to TTS engine specification."""
        # Convert to Kokoro format: "voice1:weight1,voice2:weight2"
        parts = []
        for voice_id, weight in blend.voices.items():
            weight_pct = int(weight * 100)
            parts.append(f"{voice_id}:{weight_pct}")
        
        return ",".join(parts)
    
    def detect_characters_in_text(self, text: str) -> Set[str]:
        """
        Detect character names mentioned in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Set of detected character names
        """
        detected = set()
        
        # Check for existing characters
        for char_name in self.characters.keys():
            if self._character_mentioned(char_name, text):
                detected.add(char_name)
        
        # Simple pattern-based detection for new characters
        # Look for dialogue attribution patterns
        patterns = [
            r'"[^"]+"\s*,?\s*(\w+)\s+said',
            r'(\w+)\s+said\s*,?\s*"[^"]+"',
            r'"[^"]+"\s*,?\s*asked\s+(\w+)',
            r'(\w+)\s+asked\s*,?\s*"[^"]+"',
            r'(\w+)\s+replied',
            r'(\w+)\s+whispered',
            r'(\w+)\s+shouted',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                # Filter out common words
                if self._is_likely_character_name(name):
                    detected.add(name.capitalize())
        
        return detected
    
    def _character_mentioned(self, char_name: str, text: str) -> bool:
        """Check if character is mentioned in text."""
        # Look for name in various contexts
        patterns = [
            r'\b' + re.escape(char_name) + r'\b',
            r'\b' + re.escape(char_name.lower()) + r'\b',
            r'\b' + re.escape(char_name.upper()) + r'\b'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _is_likely_character_name(self, name: str) -> bool:
        """Determine if a word is likely a character name."""
        # Filter out common words that aren't names
        common_words = {
            'he', 'she', 'they', 'it', 'i', 'you', 'we', 'us', 'them',
            'said', 'asked', 'replied', 'told', 'spoke', 'answered',
            'the', 'and', 'but', 'or', 'so', 'for', 'nor', 'yet',
            'a', 'an', 'this', 'that', 'these', 'those'
        }
        
        # Basic checks
        if name.lower() in common_words:
            return False
        
        if len(name) < 2:
            return False
        
        if not name[0].isupper():
            return False
        
        # Should be mostly alphabetic
        if not name.replace("'", "").replace("-", "").isalpha():
            return False
        
        return True
    
    def auto_assign_voices(
        self,
        character_names: Set[str],
        voice_engine: Optional[KokoroEngine] = None,
        text: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Automatically assign voices to detected characters with gender detection.

        Args:
            character_names: Set of character names to assign
            voice_engine: TTS engine for getting available voices
            text: Full text for gender detection (optional)

        Returns:
            Dict mapping character names to voice IDs
        """
        assignments = {}

        if not voice_engine:
            try:
                voice_engine = KokoroEngine()
            except:
                # Fallback to basic assignment using configured default
                from ..config import ConfigManager
                config = ConfigManager().config
                fallback_voice = config.tts.voice or "am_michael"
                return {name: fallback_voice for name in character_names}

        available_voices = voice_engine.list_voices()

        # Get male and female voices
        male_voices = voice_engine.get_voices_by_gender("male")
        female_voices = voice_engine.get_voices_by_gender("female")

        # Detect genders if text provided
        gender_map = {}
        if text:
            gender_map = self.gender_detector.detect_multiple_genders(
                list(character_names), text
            )

        # Track used voices for variety
        used_voices = set()

        for char_name in sorted(character_names):
            # Get detected gender or use unknown
            detected_gender = gender_map.get(char_name, 'unknown')

            # Select voice pool based on detected gender
            if detected_gender == 'female' and female_voices:
                voice_pool = female_voices
                gender = "female"
            elif detected_gender == 'male' and male_voices:
                voice_pool = male_voices
                gender = "male"
            else:
                # Unknown gender - alternate between male/female for variety
                if len([g for g in assignments.values() if g in male_voices]) <= len([g for g in assignments.values() if g in female_voices]):
                    voice_pool = male_voices if male_voices else available_voices
                    gender = "male" if male_voices else "unknown"
                else:
                    voice_pool = female_voices if female_voices else available_voices
                    gender = "female" if female_voices else "unknown"

            # Pick an unused voice if possible
            available_pool = [v for v in voice_pool if v not in used_voices]
            if not available_pool:
                available_pool = voice_pool

            voice_id = available_pool[0]
            used_voices.add(voice_id)

            # Add to character mapping
            self.add_character(
                name=char_name,
                voice_id=voice_id,
                gender=gender
            )

            assignments[char_name] = voice_id

        return assignments
    
    def get_narration_voice(self) -> str:
        """Get the voice to use for narration (non-dialogue text)."""
        # Check if there's a special "Narrator" character
        narrator = self.get_character_voice("Narrator")
        if narrator:
            return narrator.voice_id
        
        # Default narration voice
        # Use configured fallback voice
        from ..config import ConfigManager
        config = ConfigManager().config
        return config.tts.voice or "am_michael"  # Use configured voice or default
    
    def analyze_text_for_voices(self, text: str) -> Dict[str, any]:
        """
        Analyze text and return character/voice information.

        Returns:
            Dict with detected characters, voice assignments, and statistics
        """
        detected_chars = self.detect_characters_in_text(text)
        existing_chars = set(self.list_characters())
        new_chars = detected_chars - existing_chars

        # Auto-assign voices for new characters with gender detection
        if new_chars:
            new_assignments = self.auto_assign_voices(new_chars, text=text)
        else:
            new_assignments = {}

        # Get current assignments
        current_assignments = {
            char: self.get_character_voice(char).voice_id
            for char in existing_chars
            if char in detected_chars
        }

        all_assignments = {**current_assignments, **new_assignments}

        return {
            'detected_characters': list(detected_chars),
            'new_characters': list(new_chars),
            'existing_characters': list(existing_chars & detected_chars),
            'voice_assignments': all_assignments,
            'narration_voice': self.get_narration_voice(),
            'total_characters': len(detected_chars)
        }