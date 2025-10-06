# Kokoro TTS Setup Guide

## Overview
Reader uses Kokoro-82M, a high-quality neural TTS model with 48 voices across 8 languages. The model files are large (~300MB) and must be downloaded separately.

## Current Status
- ✅ Kokoro ONNX library installed via Poetry
- ✅ Engine implementation complete in `reader/engines/kokoro_engine.py`
- ⚠️ Model files need to be downloaded manually (large files - ~300MB total)

## Required Model Files
Download these files to `models/kokoro/`:

```bash
mkdir -p models/kokoro
cd models/kokoro

# Download model files (310MB each)
curl -L -o kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

## Installation Dependencies
Already installed via Poetry:
- `kokoro-onnx` - Main TTS library
- `soundfile` - May be needed for audio processing

## Available Voices
48 voices across 8 languages including:
- American English: af_sarah, af_nicole, af_michael, af_adam
- British English: bf_emma, bf_isabella, bf_oliver, bf_william
- Spanish: ef_clara, ef_pedro
- French: ff_marie, ff_pierre

## Usage Example
```python
from kokoro_onnx import Kokoro
kokoro = Kokoro("models/kokoro/kokoro-v1.0.onnx", "models/kokoro/voices-v1.0.bin")
samples, sample_rate = kokoro.create("Hello world!", voice="af_sarah", speed=1.0, lang="en-us")
```

## Testing After Setup

```bash
# Basic test with Neural Engine
poetry run reader convert --debug --file text/sample.txt

# Should show:
# ✅ Kokoro initialized with Neural Engine acceleration (CoreML)
# 🚀 Optimized settings: 48k mono MP3, Neural Engine acceleration

# Test with different voices
poetry run reader convert --voice af_sarah --file text/sample.txt
poetry run reader convert --voice am_michael --file text/sample.txt
poetry run reader convert --voice bf_emma --file text/sample.txt

# List all available voices
poetry run reader voices
```

## Troubleshooting

**Models not found:**
- Verify files are in `models/kokoro/` directory
- Check filenames match exactly: `kokoro-v1.0.onnx` and `voices-v1.0.bin`
- Models are ~310MB (onnx) and ~27MB (bin)

**Neural Engine not detected:**
- Apple Silicon only (M1/M2/M3 Macs)
- On Intel/Windows/Linux, uses CPU (still fast)
- Debug mode shows acceleration status: `--debug`

**Fallback to pyttsx3:**
- If models missing, automatically uses system TTS
- Lower quality but works without downloads
- Install models for professional audio quality