"""
Reader: Professional text-to-audiobook CLI with Neural Engine acceleration.

Powered by Kokoro-82M neural TTS with 54 voices across 9 languages.
Features character voice mapping, dialogue detection, and professional audio output.

For system TTS fallback support, see reader-small package.
"""

__version__ = "0.3.0"
__author__ = "danielcorsano"

# Public API
from .api import Reader, convert, list_voices

__all__ = ["Reader", "convert", "list_voices"]