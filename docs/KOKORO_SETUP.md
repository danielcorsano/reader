# Kokoro TTS Setup Guide

## Overview
Reader uses Kokoro-82M, a high-quality neural TTS model with 54 voices across 9 languages. The model files are large (~310MB) and are downloaded automatically on first use.

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

**Models not found:**
- Verify files are in `models/kokoro/` directory
- Check filenames match exactly: `kokoro-v1.0.onnx` and `voices-v1.0.bin`
- Models are ~310MB (onnx) and ~27MB (bin)

**Neural Engine not detected:**
- Apple Silicon only (M1/M2/M3 Macs)
- On Intel/Windows/Linux, uses CPU (still fast)
- Debug mode shows acceleration status: `--debug`

**Models required:**
- Kokoro models are required for this package (~300MB)
- Models auto-download to cache on first use