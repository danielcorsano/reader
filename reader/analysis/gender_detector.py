"""Lightweight gender detection using pronoun frequency analysis."""
import re
from typing import Dict, List, Tuple, Optional


class GenderDetector:
    """Detects character gender from text using pronoun pattern analysis."""

    MALE_PRONOUNS = {'he', 'him', 'his', 'himself'}
    FEMALE_PRONOUNS = {'she', 'her', 'hers', 'herself'}

    # Compiled patterns for performance
    NAME_BOUNDARY = re.compile(r'\b')
    PRONOUN_PATTERN = re.compile(
        r'\b(he|him|his|himself|she|her|hers|herself)\b',
        re.IGNORECASE
    )

    def __init__(self, context_window: int = 200):
        """
        Initialize gender detector.

        Args:
            context_window: Character radius around name mentions to analyze
        """
        self.context_window = context_window

    def detect_character_gender(
        self,
        character_name: str,
        text: str,
        min_mentions: int = 2
    ) -> str:
        """
        Detect character gender by analyzing pronouns near character mentions.

        Args:
            character_name: Name of character to analyze
            text: Full text to search
            min_mentions: Minimum character mentions required for detection

        Returns:
            'male', 'female', or 'unknown'
        """
        # Find all mentions of character
        mentions = self._find_character_mentions(character_name, text)

        if len(mentions) < min_mentions:
            return 'unknown'

        # Extract context windows around mentions
        contexts = self._extract_contexts(text, mentions)

        # Count pronouns in contexts
        male_count, female_count = self._count_pronouns(contexts)

        # Determine gender based on pronoun frequency
        return self._classify_gender(male_count, female_count)

    def detect_multiple_genders(
        self,
        character_names: List[str],
        text: str
    ) -> Dict[str, str]:
        """
        Detect genders for multiple characters efficiently.

        Args:
            character_names: List of character names
            text: Full text to analyze

        Returns:
            Dict mapping character names to detected genders
        """
        results = {}

        for name in character_names:
            # Create filtered text without other character names to reduce noise
            filtered_text = text
            for other_name in character_names:
                if other_name != name:
                    # Replace other character names with placeholder to avoid confusion
                    filtered_text = re.sub(
                        r'\b' + re.escape(other_name) + r'\b',
                        'PERSON',
                        filtered_text,
                        flags=re.IGNORECASE
                    )

            results[name] = self.detect_character_gender(name, filtered_text)

        return results

    def _find_character_mentions(self, name: str, text: str) -> List[int]:
        """Find all mention positions of character name in text."""
        mentions = []
        pattern = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)

        for match in pattern.finditer(text):
            mentions.append(match.start())

        return mentions

    def _extract_contexts(
        self,
        text: str,
        mention_positions: List[int]
    ) -> List[str]:
        """Extract context windows AFTER character mentions."""
        contexts = []
        text_len = len(text)

        for pos in mention_positions:
            # Focus on text AFTER the character mention (pronouns typically follow)
            start = pos
            end = min(text_len, pos + self.context_window)
            contexts.append(text[start:end])

        return contexts

    def _count_pronouns(self, contexts: List[str]) -> Tuple[int, int]:
        """Count male and female pronouns in context windows."""
        male_count = 0
        female_count = 0

        for context in contexts:
            # Find all pronouns in context
            pronouns = self.PRONOUN_PATTERN.findall(context.lower())

            for pronoun in pronouns:
                if pronoun in self.MALE_PRONOUNS:
                    male_count += 1
                elif pronoun in self.FEMALE_PRONOUNS:
                    female_count += 1

        return male_count, female_count

    def _classify_gender(
        self,
        male_count: int,
        female_count: int,
        confidence_threshold: float = 0.55
    ) -> str:
        """
        Classify gender based on pronoun counts.

        Args:
            male_count: Number of male pronouns found
            female_count: Number of female pronouns found
            confidence_threshold: Minimum ratio for confident classification

        Returns:
            'male', 'female', or 'unknown'
        """
        total = male_count + female_count

        # Need at least 3 pronouns for detection
        if total < 3:
            return 'unknown'

        male_ratio = male_count / total
        female_ratio = female_count / total

        if male_ratio >= confidence_threshold:
            return 'male'
        elif female_ratio >= confidence_threshold:
            return 'female'
        else:
            return 'unknown'

    def get_gender_statistics(
        self,
        character_name: str,
        text: str
    ) -> Dict[str, any]:
        """
        Get detailed gender detection statistics for debugging.

        Args:
            character_name: Name of character
            text: Full text to analyze

        Returns:
            Dict with mentions, pronoun counts, and confidence scores
        """
        mentions = self._find_character_mentions(character_name, text)
        contexts = self._extract_contexts(text, mentions)
        male_count, female_count = self._count_pronouns(contexts)

        total = male_count + female_count

        return {
            'character': character_name,
            'mentions': len(mentions),
            'male_pronouns': male_count,
            'female_pronouns': female_count,
            'male_ratio': male_count / total if total > 0 else 0,
            'female_ratio': female_count / total if total > 0 else 0,
            'detected_gender': self._classify_gender(male_count, female_count),
            'confidence': max(male_count, female_count) / total if total > 0 else 0
        }
