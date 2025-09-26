"""Emotion detection using VADER sentiment analysis."""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False


@dataclass
class EmotionAnalysis:
    """Container for emotion analysis results."""
    sentiment_score: float  # -1 (negative) to 1 (positive)
    emotion: str  # dominant emotion category
    intensity: str  # low, medium, high
    confidence: float  # 0 to 1
    prosody_hints: Dict[str, float]  # SSML prosody adjustments


class EmotionDetector:
    """Detects emotions in text using VADER and rule-based patterns."""
    
    # Emotion keywords and their sentiment associations
    EMOTION_PATTERNS = {
        'excited': {'keywords': ['excited', 'thrilled', 'amazing', 'incredible', 'fantastic'], 'sentiment': 0.8},
        'happy': {'keywords': ['happy', 'joyful', 'delighted', 'pleased', 'cheerful'], 'sentiment': 0.6},
        'angry': {'keywords': ['angry', 'furious', 'mad', 'rage', 'outraged'], 'sentiment': -0.7},
        'sad': {'keywords': ['sad', 'depressed', 'miserable', 'heartbroken', 'devastated'], 'sentiment': -0.6},
        'fearful': {'keywords': ['scared', 'terrified', 'afraid', 'frightened', 'worried'], 'sentiment': -0.4},
        'surprised': {'keywords': ['surprised', 'shocked', 'stunned', 'astonished'], 'sentiment': 0.2},
        'calm': {'keywords': ['calm', 'peaceful', 'serene', 'tranquil', 'relaxed'], 'sentiment': 0.1},
        'neutral': {'keywords': ['said', 'stated', 'mentioned', 'noted', 'observed'], 'sentiment': 0.0}
    }
    
    # Punctuation-based emotion hints
    PUNCTUATION_EMOTIONS = {
        '!': {'emotion': 'excited', 'intensity_boost': 0.3},
        '?': {'emotion': 'curious', 'intensity_boost': 0.1},
        '...': {'emotion': 'hesitant', 'intensity_boost': 0.2},
        '!!': {'emotion': 'very_excited', 'intensity_boost': 0.5},
        '?!': {'emotion': 'surprised', 'intensity_boost': 0.4}
    }
    
    def __init__(self):
        """Initialize the emotion detector."""
        if not VADER_AVAILABLE:
            raise ImportError("VADER sentiment not available. Install with: poetry add vaderSentiment")
        
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze_emotion(self, text: str) -> EmotionAnalysis:
        """
        Analyze emotion in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            EmotionAnalysis with detected emotion and prosody hints
        """
        # VADER sentiment analysis
        scores = self.analyzer.polarity_scores(text)
        sentiment_score = scores['compound']
        
        # Rule-based emotion detection
        detected_emotion = self._detect_emotion_patterns(text)
        
        # Punctuation analysis
        punct_emotion = self._analyze_punctuation(text)
        
        # Combine results
        final_emotion = detected_emotion or punct_emotion or self._sentiment_to_emotion(sentiment_score)
        intensity = self._calculate_intensity(sentiment_score, text)
        confidence = abs(sentiment_score) * 0.7 + (0.3 if detected_emotion else 0)
        
        # Generate prosody hints
        prosody_hints = self._generate_prosody_hints(final_emotion, sentiment_score, intensity)
        
        return EmotionAnalysis(
            sentiment_score=sentiment_score,
            emotion=final_emotion,
            intensity=intensity,
            confidence=min(confidence, 1.0),
            prosody_hints=prosody_hints
        )
    
    def analyze_dialogue(self, text: str) -> Tuple[str, EmotionAnalysis]:
        """
        Analyze dialogue with speaker detection.
        
        Args:
            text: Text that may contain dialogue
            
        Returns:
            Tuple of (speaker_or_narration, emotion_analysis)
        """
        # Simple dialogue detection
        if self._is_dialogue(text):
            return "dialogue", self.analyze_emotion(text)
        else:
            return "narration", self.analyze_emotion(text)
    
    def _detect_emotion_patterns(self, text: str) -> Optional[str]:
        """Detect emotions using keyword patterns."""
        text_lower = text.lower()
        
        emotion_scores = {}
        for emotion, data in self.EMOTION_PATTERNS.items():
            score = 0
            for keyword in data['keywords']:
                if keyword in text_lower:
                    score += 1
            
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _analyze_punctuation(self, text: str) -> Optional[str]:
        """Detect emotions from punctuation patterns."""
        for punct, emotion_data in self.PUNCTUATION_EMOTIONS.items():
            if punct in text:
                return emotion_data['emotion']
        
        return None
    
    def _sentiment_to_emotion(self, sentiment_score: float) -> str:
        """Convert VADER sentiment score to emotion category."""
        if sentiment_score >= 0.5:
            return 'happy'
        elif sentiment_score >= 0.1:
            return 'positive'
        elif sentiment_score <= -0.5:
            return 'sad'
        elif sentiment_score <= -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_intensity(self, sentiment_score: float, text: str) -> str:
        """Calculate emotion intensity."""
        base_intensity = abs(sentiment_score)
        
        # Boost intensity for caps, multiple punctuation
        if text.isupper():
            base_intensity += 0.3
        if '!!' in text or '???' in text:
            base_intensity += 0.2
        
        if base_intensity >= 0.7:
            return 'high'
        elif base_intensity >= 0.3:
            return 'medium'
        else:
            return 'low'
    
    def _generate_prosody_hints(self, emotion: str, sentiment_score: float, intensity: str) -> Dict[str, float]:
        """Generate SSML prosody hints based on emotion."""
        prosody = {
            'rate': 1.0,      # Speech rate multiplier
            'pitch': 0.0,     # Pitch offset (-100 to +100)
            'volume': 1.0     # Volume multiplier
        }
        
        # Base adjustments by emotion
        emotion_prosody = {
            'excited': {'rate': 1.3, 'pitch': 20, 'volume': 1.1},
            'happy': {'rate': 1.1, 'pitch': 10, 'volume': 1.0},
            'angry': {'rate': 1.2, 'pitch': -10, 'volume': 1.2},
            'sad': {'rate': 0.8, 'pitch': -20, 'volume': 0.9},
            'fearful': {'rate': 1.4, 'pitch': 15, 'volume': 0.8},
            'surprised': {'rate': 1.2, 'pitch': 25, 'volume': 1.0},
            'calm': {'rate': 0.9, 'pitch': -5, 'volume': 0.9},
            'neutral': {'rate': 1.0, 'pitch': 0, 'volume': 1.0}
        }
        
        if emotion in emotion_prosody:
            base = emotion_prosody[emotion]
            prosody.update(base)
        
        # Intensity adjustments
        intensity_multipliers = {
            'low': 0.5,
            'medium': 0.8,
            'high': 1.2
        }
        
        multiplier = intensity_multipliers.get(intensity, 1.0)
        prosody['pitch'] *= multiplier
        prosody['rate'] = 1.0 + (prosody['rate'] - 1.0) * multiplier
        
        # Clamp values to reasonable ranges
        prosody['rate'] = max(0.5, min(2.0, prosody['rate']))
        prosody['pitch'] = max(-50, min(50, prosody['pitch']))
        prosody['volume'] = max(0.5, min(1.5, prosody['volume']))
        
        return prosody
    
    def _is_dialogue(self, text: str) -> bool:
        """Simple dialogue detection."""
        # Check for quote marks
        if '"' in text or "'" in text:
            return True
        
        # Check for dialogue tags
        dialogue_patterns = [
            r'he said', r'she said', r'they said',
            r'he asked', r'she asked', r'they asked',
            r'he replied', r'she replied', r'they replied',
            r'he whispered', r'she whispered', r'they whispered',
            r'he shouted', r'she shouted', r'they shouted'
        ]
        
        text_lower = text.lower()
        for pattern in dialogue_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def get_emotion_summary(self, analyses: List[EmotionAnalysis]) -> Dict[str, float]:
        """Get summary statistics for a list of emotion analyses."""
        if not analyses:
            return {}
        
        emotions = [a.emotion for a in analyses]
        sentiment_scores = [a.sentiment_score for a in analyses]
        
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Normalize to percentages
        total = len(emotions)
        emotion_percentages = {e: count/total for e, count in emotion_counts.items()}
        
        return {
            'dominant_emotion': max(emotion_counts.items(), key=lambda x: x[1])[0],
            'average_sentiment': sum(sentiment_scores) / len(sentiment_scores),
            'emotion_distribution': emotion_percentages,
            'total_segments': total
        }