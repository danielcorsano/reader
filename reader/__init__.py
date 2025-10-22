"""
Reader: Professional text-to-audiobook CLI with Neural Engine acceleration.

Powered by Kokoro-82M neural TTS with 54 voices across 9 languages.
Features emotion detection, character voice mapping, and professional audio output.

For system TTS fallback support, see reader-small package.
"""

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("audiobook-reader")
except Exception:
    __version__ = "0.1.7"  # fallback if metadata not available

__author__ = "danielcorsano"

# Public API
from .api import Reader, convert, list_voices

__all__ = ["Reader", "convert", "list_voices"]