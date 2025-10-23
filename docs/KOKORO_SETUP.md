# Kokoro TTS Setup Guide

## Overview
Reader uses Kokoro-82M, a high-quality neural TTS model with 54 voices across 9 languages.

## Current Status
- ✅ Kokoro ONNX library installed
- ✅ Engine implementation complete
- ✅ **Models auto-download on first use** (~310MB to `~/.cache/audiobook-reader/models/`)

## Model Download

Models automatically download to system cache on first use. No manual setup required!

**Manual download** (optional):
```bash
# Auto-download to cache (default)
reader download models

# Force re-download
reader download models --force

# Download to local models/ folder (development)
reader download models --local
```

## Installation Dependencies
Already installed via Poetry:
- `kokoro-onnx` - Main TTS library
- `soundfile` - May be needed for audio processing

## Available Voices
54 voices across 9 languages including:
- American English (20 voices): af_heart, af_alloy, af_aoede, af_bella, af_jessica, af_kore, af_nicole, af_nova, af_river, af_sarah, af_sky, am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck, am_santa
- British English (8 voices): bf_alice, bf_emma, bf_isabella, bf_lily, bm_daniel, bm_fable, bm_george, bm_lewis
- Japanese (5 voices): jf_alpha, jf_gongitsune, jf_nezumi, jf_tebukuro, jm_kumo
- Mandarin Chinese (8 voices): zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zf_xiaoyi, zm_yunjian, zm_yunxi, zm_yunxia, zm_yunyang
- Spanish (3 voices): ef_dora, em_alex, em_santa
- French (1 voice): ff_siwis
- Hindi (4 voices): hf_alpha, hf_beta, hm_omega, hm_psi
- Italian (2 voices): if_sara, im_nicola
- Brazilian Portuguese (3 voices): pf_dora, pm_alex, pm_santa

## Usage Example
```python
from kokoro_onnx import Kokoro
kokoro = Kokoro("models/kokoro/kokoro-v1.0.onnx", "models/kokoro/voices-v1.0.bin")
samples, sample_rate = kokoro.create("Hello world!", voice="af_sarah", speed=1.0, lang="en-us")
```

## Testing After Setup

```bash
# Basic test with Neural Engine
reader convert --debug --file text/sample.txt

# Should show:
# ✅ Kokoro initialized with Neural Engine acceleration (CoreML)
# 🚀 Optimized settings: 48k mono MP3, Neural Engine acceleration

# Test with different voices
reader convert --voice af_sarah --file text/sample.txt
reader convert --voice am_michael --file text/sample.txt
reader convert --voice bf_emma --file text/sample.txt

# List all available voices
reader voices
```

## Troubleshooting

**Models not downloading:**
- Check internet connection
- Try manual download: `reader download models`
- Models cache: `~/.cache/audiobook-reader/models/`
- Total size: ~310MB (kokoro-v1.0.onnx) + ~27MB (voices-v1.0.bin)

**Neural Engine not detected:**
- Apple Silicon only (M1/M2/M3/M4 Macs)
- On Intel/Windows/Linux, uses CPU (still fast)
- Debug mode shows acceleration status: `--debug`

**FFmpeg not found:**
- Required for audio conversion
- macOS: `brew install ffmpeg`
- Windows: `winget install ffmpeg`
- Linux: `sudo apt install ffmpeg`