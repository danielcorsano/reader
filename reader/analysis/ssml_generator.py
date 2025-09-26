"""SSML generation for smart prosody and acting based on emotion analysis."""
import re
from typing import Dict, List, Optional, Tuple
from xml.sax.saxutils import escape

from .emotion_detector import EmotionDetector, EmotionAnalysis


class SSMLGenerator:
    """Generates SSML markup for enhanced text-to-speech with prosody and acting."""
    
    # Punctuation-based prosody rules
    PUNCTUATION_RULES = {
        '!': {'emphasis': 'strong', 'rate': '+10%', 'pitch': '+5st'},
        '?': {'pitch': '+3st', 'rate': '+5%'},
        '...': {'rate': '-20%', 'pause': '0.5s'},
        ',': {'pause': '0.2s'},
        ';': {'pause': '0.3s'},
        ':': {'pause': '0.4s'},
        '.': {'pause': '0.6s'},
        '!!': {'emphasis': 'strong', 'rate': '+20%', 'pitch': '+10st'},
        '???': {'pitch': '+8st', 'rate': '+15%'},
    }
    
    # Context-based acting rules
    CONTEXT_RULES = {
        'whispered': {'volume': 'soft', 'rate': '-10%'},
        'shouted': {'volume': 'loud', 'rate': '+15%', 'emphasis': 'strong'},
        'screamed': {'volume': 'loud', 'rate': '+25%', 'pitch': '+15st'},
        'murmured': {'volume': 'soft', 'rate': '-15%', 'pitch': '-3st'},
        'growled': {'pitch': '-10st', 'rate': '-5%'},
        'sighed': {'rate': '-20%', 'pitch': '-5st'},
        'laughed': {'rate': '+10%', 'pitch': '+5st'},
        'cried': {'pitch': '+8st', 'volume': 'soft'},
        'yelled': {'volume': 'loud', 'rate': '+20%'},
        'mumbled': {'rate': '-25%', 'volume': 'soft'},
    }
    
    def __init__(self):
        """Initialize SSML generator."""
        self.emotion_detector = EmotionDetector()
    
    def generate_ssml(
        self, 
        text: str, 
        emotion_analysis: Optional[EmotionAnalysis] = None,
        apply_punctuation_rules: bool = True,
        apply_context_rules: bool = True,
        apply_emotion_prosody: bool = True
    ) -> str:
        """
        Generate SSML markup for text with emotion-based prosody.
        
        Args:
            text: Input text
            emotion_analysis: Pre-computed emotion analysis (optional)
            apply_punctuation_rules: Apply punctuation-based prosody
            apply_context_rules: Apply context keyword prosody  
            apply_emotion_prosody: Apply emotion-based prosody
            
        Returns:
            SSML-enhanced text
        """
        if not emotion_analysis:
            emotion_analysis = self.emotion_detector.analyze_emotion(text)
        
        # Start with escaped text
        ssml_text = escape(text)
        
        # Apply different enhancement layers
        if apply_context_rules:
            ssml_text = self._apply_context_rules(ssml_text)
        
        if apply_emotion_prosody:
            ssml_text = self._apply_emotion_prosody(ssml_text, emotion_analysis)
        
        if apply_punctuation_rules:
            ssml_text = self._apply_punctuation_rules(ssml_text)
        
        # Wrap in SSML speak tags
        return f'<speak>{ssml_text}</speak>'
    
    def generate_dialogue_ssml(
        self, 
        text: str, 
        character: Optional[str] = None,
        emotion: Optional[str] = None
    ) -> str:
        """
        Generate SSML for dialogue with character-specific prosody.
        
        Args:
            text: Dialogue text
            character: Character name for voice mapping
            emotion: Override emotion detection
            
        Returns:
            SSML-enhanced dialogue
        """
        # Analyze emotion if not provided
        if emotion:
            # Create mock emotion analysis
            emotion_analysis = EmotionAnalysis(
                sentiment_score=0.0,
                emotion=emotion,
                intensity='medium',
                confidence=0.8,
                prosody_hints={'rate': 1.0, 'pitch': 0.0, 'volume': 1.0}
            )
        else:
            emotion_analysis = self.emotion_detector.analyze_emotion(text)
        
        # Generate base SSML
        ssml_text = self.generate_ssml(text, emotion_analysis)
        
        # Add character-specific voice if supported
        if character:
            # This would be handled by voice mapping in Phase 3
            # For now, add a comment
            ssml_text = f'<!-- Character: {character} -->{ssml_text}'
        
        return ssml_text
    
    def _apply_emotion_prosody(self, text: str, emotion_analysis: EmotionAnalysis) -> str:
        """Apply emotion-based prosody to text."""
        prosody_hints = emotion_analysis.prosody_hints
        
        # Convert prosody hints to SSML attributes
        prosody_attrs = []
        
        if prosody_hints.get('rate', 1.0) != 1.0:
            rate_pct = int((prosody_hints['rate'] - 1.0) * 100)
            rate_sign = '+' if rate_pct >= 0 else ''
            prosody_attrs.append(f'rate="{rate_sign}{rate_pct}%"')
        
        if prosody_hints.get('pitch', 0.0) != 0.0:
            pitch_st = int(prosody_hints['pitch'] / 5)  # Convert to semitones
            pitch_sign = '+' if pitch_st >= 0 else ''
            prosody_attrs.append(f'pitch="{pitch_sign}{pitch_st}st"')
        
        if prosody_hints.get('volume', 1.0) != 1.0:
            volume = prosody_hints['volume']
            if volume > 1.1:
                prosody_attrs.append('volume="loud"')
            elif volume < 0.9:
                prosody_attrs.append('volume="soft"')
        
        # Wrap text in prosody tag if attributes exist
        if prosody_attrs:
            attrs_str = ' '.join(prosody_attrs)
            return f'<prosody {attrs_str}>{text}</prosody>'
        
        return text
    
    def _apply_context_rules(self, text: str) -> str:
        """Apply context-based acting rules."""
        text_lower = text.lower()
        
        for context_word, prosody in self.CONTEXT_RULES.items():
            if context_word in text_lower:
                # Find the position and apply prosody around it
                pattern = re.compile(r'\b' + re.escape(context_word) + r'\b', re.IGNORECASE)
                
                def replace_with_prosody(match):
                    word = match.group(0)
                    attrs = []
                    
                    for attr, value in prosody.items():
                        if attr in ['rate', 'pitch', 'volume']:
                            attrs.append(f'{attr}="{value}"')
                        elif attr == 'emphasis':
                            return f'<emphasis level="{value}">{word}</emphasis>'
                    
                    if attrs:
                        attrs_str = ' '.join(attrs)
                        return f'<prosody {attrs_str}>{word}</prosody>'
                    
                    return word
                
                text = pattern.sub(replace_with_prosody, text)
        
        return text
    
    def _apply_punctuation_rules(self, text: str) -> str:
        """Apply punctuation-based prosody rules."""
        # Process in order of complexity (longer patterns first)
        punctuation_order = sorted(self.PUNCTUATION_RULES.keys(), key=len, reverse=True)
        
        for punct in punctuation_order:
            if punct in text:
                rules = self.PUNCTUATION_RULES[punct]
                
                # Replace punctuation with SSML
                if 'pause' in rules:
                    # Add break after punctuation
                    text = text.replace(punct, f'{punct}<break time="{rules["pause"]}"/>')
                
                # Apply emphasis or prosody to words before punctuation
                if any(attr in rules for attr in ['emphasis', 'rate', 'pitch', 'volume']):
                    # Find words followed by this punctuation
                    pattern = r'(\S+)' + re.escape(punct)
                    
                    def add_prosody(match):
                        word = match.group(1)
                        
                        if 'emphasis' in rules:
                            word = f'<emphasis level="{rules["emphasis"]}">{word}</emphasis>'
                        
                        prosody_attrs = []
                        for attr in ['rate', 'pitch', 'volume']:
                            if attr in rules:
                                prosody_attrs.append(f'{attr}="{rules[attr]}"')
                        
                        if prosody_attrs:
                            attrs_str = ' '.join(prosody_attrs)
                            word = f'<prosody {attrs_str}>{word}</prosody>'
                        
                        return word + punct
                    
                    text = re.sub(pattern, add_prosody, text)
        
        return text
    
    def process_chapter(self, text: str, chapter_title: Optional[str] = None) -> str:
        """Process an entire chapter with SSML enhancement."""
        # Split into sentences for better emotion analysis
        sentences = self._split_sentences(text)
        ssml_sentences = []
        
        # Add chapter title if provided
        if chapter_title:
            title_ssml = f'<prosody rate="-10%" pitch="+2st"><emphasis level="moderate">{escape(chapter_title)}</emphasis></prosody>'
            title_ssml += '<break time="1s"/>'
            ssml_sentences.append(title_ssml)
        
        # Process each sentence
        for sentence in sentences:
            if sentence.strip():
                sentence_ssml = self.generate_ssml(sentence.strip())
                # Remove outer <speak> tags since we'll add them at the end
                sentence_ssml = sentence_ssml.replace('<speak>', '').replace('</speak>', '')
                ssml_sentences.append(sentence_ssml)
        
        # Combine with chapter breaks
        chapter_ssml = '<break time="0.3s"/>'.join(ssml_sentences)
        
        return f'<speak>{chapter_ssml}</speak>'
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving context."""
        # Simple sentence splitting - can be enhanced
        sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def create_character_voice_map(self, text: str) -> Dict[str, List[str]]:
        """
        Analyze text to create character-to-dialogue mapping.
        Returns mapping of character names to their dialogue lines.
        """
        character_map = {}
        
        # Find dialogue patterns with speaker attribution
        dialogue_patterns = [
            r'"([^"]+)"\s*,?\s*(he|she|they|\w+)\s+(said|asked|replied|whispered|shouted)',
            r'(\w+)\s+(said|asked|replied|whispered|shouted)\s*,?\s*"([^"]+)"',
            r'"([^"]+)"\s*,?\s*said\s+(\w+)',
        ]
        
        for pattern in dialogue_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    # Extract dialogue and speaker
                    dialogue = None
                    speaker = None
                    
                    for group in groups:
                        if '"' in group or len(group) > 20:  # Likely dialogue
                            dialogue = group.strip('"')
                        elif group.lower() not in ['said', 'asked', 'replied', 'whispered', 'shouted', 'he', 'she', 'they']:
                            speaker = group.capitalize()
                    
                    if dialogue and speaker:
                        if speaker not in character_map:
                            character_map[speaker] = []
                        character_map[speaker].append(dialogue)
        
        return character_map
    
    def optimize_ssml_for_tts(self, ssml: str, tts_engine: str = 'kokoro') -> str:
        """
        Optimize SSML for specific TTS engines.
        
        Args:
            ssml: SSML text to optimize
            tts_engine: Target TTS engine ('kokoro', 'pyttsx3', etc.)
            
        Returns:
            Optimized SSML
        """
        if tts_engine == 'kokoro':
            # Kokoro might not support all SSML tags, simplify
            # Remove unsupported tags but keep the text
            ssml = re.sub(r'<emphasis[^>]*>(.*?)</emphasis>', r'\1', ssml)
            ssml = re.sub(r'<prosody[^>]*>(.*?)</prosody>', r'\1', ssml)
            # Keep breaks as they're commonly supported
        
        elif tts_engine == 'pyttsx3':
            # pyttsx3 has very limited SSML support, strip most tags
            ssml = re.sub(r'<[^>]+>', '', ssml)  # Remove all tags except speak
            ssml = f'<speak>{ssml}</speak>'
        
        return ssml