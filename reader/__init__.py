"""
Reader: Professional text-to-audiobook CLI with Neural Engine acceleration.

Powered by Kokoro-82M neural TTS with 54 voices across 9 languages.
Features character voice mapping, dialogue detection, and professional audio output.

For system TTS fallback support, see reader-small package.
"""

import os

# Opt out of onnxruntime's default-on telemetry; must be set before onnxruntime initializes
os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")

__version__ = "0.4.6"
__author__ = "danielcorsano"

# Public API
from .api import Reader, convert, list_voices  # noqa: E402

__all__ = ["Reader", "convert", "list_voices"]