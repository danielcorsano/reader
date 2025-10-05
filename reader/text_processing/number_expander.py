"""Number expansion for TTS pronunciation.

This module provides regex-based number-to-words conversion optimized for
text-to-speech synthesis. It handles:
- Cardinal numbers (1234 → "one thousand two hundred thirty-four")
- Ordinals (21st → "twenty-first")
- Decimals (3.14 → "three point one four")
- Currency ($50 → "fifty dollars")
- Percentages (25% → "twenty-five percent")
- Time (3:45 PM → "three forty-five P M")
- Ranges (5-10 → "five to ten")
- Years (1984 → "nineteen eighty-four")

Performance optimized with pre-compiled regex patterns for minimal overhead.
"""
import re
from typing import Dict, List


class NumberExpander:
    """Expands numbers and numeric expressions to words for TTS.

    Uses pre-compiled regex patterns for fast pattern matching and
    lookup tables for efficient number-to-words conversion.

    Example:
        >>> expander = NumberExpander()
        >>> expander.expand_numbers("I have 5 apples and $3.50")
        'I have five apples and three dollars and fifty cents'
    """

    # Pre-compiled regex patterns (class-level for performance)
    CURRENCY_PATTERN = re.compile(r'\$(\d{1,3}(?:,\d{3})*|\d+)(?:\.(\d{2}))?')
    TIME_PATTERN = re.compile(r'\b(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?\b')
    FRACTION_PATTERN = re.compile(r'\b(\d+)\/(\d+)\b')  # Must come before decimals
    PERCENTAGE_PATTERN = re.compile(r'\b(\d+(?:\.\d+)?)%')
    ORDINAL_PATTERN = re.compile(r'\b(\d+)(st|nd|rd|th)\b', re.IGNORECASE)
    DECIMAL_PATTERN = re.compile(r'\b(\d+)\.(\d+)\b')
    RANGE_PATTERN = re.compile(r'\b(\d+)[-–—](\d+)\b')  # Includes en/em dashes
    YEAR_PATTERN = re.compile(r'\b(1[0-9]{3}|20[0-9]{2})\b')  # 1000-2099
    CARDINAL_PATTERN = re.compile(r'\b(\d{1,3}(?:,\d{3})*|\d+)\b')

    def __init__(self):
        """Initialize number expander with lookup tables."""
        # Basic lookup tables for number conversion
        self.ones = [
            "", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine"
        ]

        self.teens = [
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen"
        ]

        self.tens = [
            "", "", "twenty", "thirty", "forty", "fifty", "sixty",
            "seventy", "eighty", "ninety"
        ]

        self.scales = ["", "thousand", "million", "billion"]

        # Special ordinals (irregular forms)
        self.special_ordinals = {
            1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
            8: "eighth", 9: "ninth", 12: "twelfth", 20: "twentieth",
            21: "twenty-first", 22: "twenty-second", 23: "twenty-third",
            30: "thirtieth", 40: "fortieth", 50: "fiftieth",
            60: "sixtieth", 70: "seventieth", 80: "eightieth", 90: "ninetieth"
        }

        # Common fractions (for natural pronunciation)
        self.common_fractions = {
            (1, 2): "one half", (1, 3): "one third", (2, 3): "two thirds",
            (1, 4): "one quarter", (3, 4): "three quarters",
            (1, 5): "one fifth", (2, 5): "two fifths", (3, 5): "three fifths", (4, 5): "four fifths",
            (1, 8): "one eighth", (3, 8): "three eighths", (5, 8): "five eighths", (7, 8): "seven eighths"
        }

    def expand_numbers(self, text: str) -> str:
        """Expand all numeric expressions to words.

        Processes in priority order (most specific to least specific):
        1. Currency ($50.00)
        2. Time (3:45 PM)
        3. Fractions (1/2)
        4. Percentages (25%)
        5. Ordinals (21st)
        6. Decimals (3.14)
        7. Ranges (5-10)
        8. Years (2024)
        9. Cardinals (1000)

        Args:
            text: Input text with numbers

        Returns:
            Text with numbers expanded to words
        """
        text = self._expand_currency(text)
        text = self._expand_time(text)
        text = self._expand_fractions(text)
        text = self._expand_percentages(text)
        text = self._expand_ordinals(text)
        text = self._expand_decimals(text)
        text = self._expand_ranges(text)
        text = self._expand_years(text)
        text = self._expand_cardinals(text)
        return text

    def _number_to_words(self, num: int) -> str:
        """Convert integer to words (supports 0 to 999,999,999,999).

        Args:
            num: Integer to convert

        Returns:
            Number as words (e.g., 1234 → "one thousand two hundred thirty-four")
        """
        if num == 0:
            return "zero"

        if num < 0:
            return "negative " + self._number_to_words(-num)

        # Handle 1-9
        if num < 10:
            return self.ones[num]

        # Handle 10-19
        if num < 20:
            return self.teens[num - 10]

        # Handle 20-99
        if num < 100:
            tens_digit = self.tens[num // 10]
            ones_digit = self.ones[num % 10]
            return tens_digit + ("-" + ones_digit if ones_digit else "")

        # Handle 100-999
        if num < 1000:
            hundreds = self.ones[num // 100] + " hundred"
            remainder = num % 100
            if remainder:
                hundreds += " and " + self._number_to_words(remainder)
            return hundreds

        # Handle thousands, millions, billions
        for i, scale in enumerate(reversed(self.scales[1:])):  # Skip empty string
            power = len(self.scales) - i - 1
            divisor = 1000 ** power

            if num >= divisor:
                high_part = num // divisor
                low_part = num % divisor

                result = self._number_to_words(high_part) + " " + scale

                if low_part:
                    result += " " + self._number_to_words(low_part)

                return result

        return str(num)  # Fallback

    def _expand_cardinals(self, text: str) -> str:
        """Expand cardinal numbers: 1234 → one thousand two hundred thirty-four.

        Args:
            text: Text containing cardinal numbers

        Returns:
            Text with cardinals expanded
        """
        def replacer(match):
            num_str = match.group(1).replace(',', '')
            try:
                num = int(num_str)
                return self._number_to_words(num)
            except ValueError:
                return match.group(0)  # Return original if conversion fails

        return self.CARDINAL_PATTERN.sub(replacer, text)

    def _expand_ordinals(self, text: str) -> str:
        """Expand ordinals: 1st → first, 21st → twenty-first.

        Args:
            text: Text containing ordinal numbers

        Returns:
            Text with ordinals expanded
        """
        def replacer(match):
            num = int(match.group(1))

            # Check special cases
            if num in self.special_ordinals:
                return self.special_ordinals[num]

            # Get cardinal words
            words = self._number_to_words(num)

            # Convert to ordinal
            if words.endswith("y"):
                # twenty → twentieth
                return words[:-1] + "ieth"
            else:
                # four → fourth, twenty-three → twenty-third
                return words + "th"

        return self.ORDINAL_PATTERN.sub(replacer, text)

    def _expand_decimals(self, text: str) -> str:
        """Expand decimals: 3.14 → three point one four.

        Args:
            text: Text containing decimal numbers

        Returns:
            Text with decimals expanded
        """
        def replacer(match):
            whole = int(match.group(1))
            fraction = match.group(2)

            result = self._number_to_words(whole) + " point"

            # Read each digit individually
            for digit in fraction:
                result += " " + self.ones[int(digit)]

            return result

        return self.DECIMAL_PATTERN.sub(replacer, text)

    def _expand_currency(self, text: str) -> str:
        """Expand currency: $50 → fifty dollars, $3.50 → three dollars and fifty cents.

        Args:
            text: Text containing currency amounts

        Returns:
            Text with currency expanded
        """
        def replacer(match):
            dollars_str = match.group(1).replace(',', '')
            cents_str = match.group(2)

            dollars = int(dollars_str)
            cents = int(cents_str) if cents_str else 0

            result = self._number_to_words(dollars)
            result += " dollar" if dollars == 1 else " dollars"

            if cents:
                result += " and " + self._number_to_words(cents)
                result += " cent" if cents == 1 else " cents"

            return result

        return self.CURRENCY_PATTERN.sub(replacer, text)

    def _expand_percentages(self, text: str) -> str:
        """Expand percentages: 25% → twenty-five percent.

        Args:
            text: Text containing percentages

        Returns:
            Text with percentages expanded
        """
        def replacer(match):
            value = float(match.group(1))

            # Handle decimals in percentages
            if '.' in match.group(1):
                # 25.5% → twenty-five point five percent
                parts = match.group(1).split('.')
                whole = int(parts[0])
                fraction = parts[1]

                result = self._number_to_words(whole) + " point"
                for digit in fraction:
                    result += " " + self.ones[int(digit)]
                result += " percent"
            else:
                # 25% → twenty-five percent
                result = self._number_to_words(int(value)) + " percent"

            return result

        return self.PERCENTAGE_PATTERN.sub(replacer, text)

    def _expand_time(self, text: str) -> str:
        """Expand time: 3:45 PM → three forty-five P M.

        Spaces out AM/PM for better TTS pronunciation.

        Args:
            text: Text containing time expressions

        Returns:
            Text with time expanded
        """
        def replacer(match):
            hours = int(match.group(1))
            minutes = int(match.group(2))
            meridiem = match.group(3)

            result = self._number_to_words(hours)

            if minutes == 0:
                result += " o'clock"
            else:
                result += " " + self._number_to_words(minutes)

            if meridiem:
                # Space out AM/PM for better pronunciation
                result += " " + " ".join(meridiem.upper())

            return result

        return self.TIME_PATTERN.sub(replacer, text)

    def _expand_fractions(self, text: str) -> str:
        """Expand fractions: 1/2 → one half, 3/4 → three quarters, 5/8 → five eighths.

        Args:
            text: Text containing fractions

        Returns:
            Text with fractions expanded
        """
        def replacer(match):
            numerator = int(match.group(1))
            denominator = int(match.group(2))

            # Check common fractions lookup
            if (numerator, denominator) in self.common_fractions:
                return self.common_fractions[(numerator, denominator)]

            # Generate fraction: "numerator denominator(s)"
            num_words = self._number_to_words(numerator)

            # Get ordinal for denominator (third, fourth, fifth, etc.)
            if denominator in self.special_ordinals:
                denom_words = self.special_ordinals[denominator]
            else:
                denom_words = self._number_to_words(denominator)
                # Convert to ordinal form
                if denom_words.endswith("y"):
                    denom_words = denom_words[:-1] + "ieth"
                else:
                    denom_words = denom_words + "th"

            # Pluralize if numerator > 1
            if numerator > 1 and not denom_words.endswith("s"):
                denom_words += "s"

            return num_words + " " + denom_words

        return self.FRACTION_PATTERN.sub(replacer, text)

    def _expand_ranges(self, text: str) -> str:
        """Expand ranges: 5-10 → five to ten.

        Args:
            text: Text containing number ranges

        Returns:
            Text with ranges expanded
        """
        def replacer(match):
            start = int(match.group(1))
            end = int(match.group(2))

            return self._number_to_words(start) + " to " + self._number_to_words(end)

        return self.RANGE_PATTERN.sub(replacer, text)

    def _expand_years(self, text: str) -> str:
        """Expand years: 1984 → nineteen eighty-four, 2024 → twenty twenty-four.

        Only expands 4-digit numbers that look like years (1000-2099).
        Context-sensitive to avoid expanding other 4-digit numbers.

        Args:
            text: Text containing year numbers

        Returns:
            Text with years expanded
        """
        def replacer(match):
            year = int(match.group(1))

            # For years 2000-2009, read as "two thousand [and] X"
            if 2000 <= year <= 2009:
                if year == 2000:
                    return "two thousand"
                else:
                    ones = year % 10
                    return "two thousand " + self.ones[ones]

            # For other years, split into two parts
            first_two = year // 100
            last_two = year % 100

            result = self._number_to_words(first_two)

            if last_two == 0:
                result += " hundred"
            else:
                result += " " + self._number_to_words(last_two)

            return result

        return self.YEAR_PATTERN.sub(replacer, text)


# Singleton instance for reuse across the application
_expander = None


def get_number_expander() -> NumberExpander:
    """Get singleton number expander instance.

    Returns:
        Shared NumberExpander instance with pre-compiled patterns
    """
    global _expander
    if _expander is None:
        _expander = NumberExpander()
    return _expander
