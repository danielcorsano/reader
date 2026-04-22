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

54 voices across 9 languages. Grades reflect training data quality and quantity (from [Kokoro-82M VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)). Voices perform best on 100-200 tokens; may rush on 400+.

### American English (20 voices)

| Voice | Gender | Grade | Notes |
|-------|--------|-------|-------|
| af_heart | F | A | Best overall quality |
| af_bella | F | A- | High quality, long training data |
| af_nicole | F | B- | Long training data |
| af_aoede | F | C+ | |
| af_kore | F | C+ | |
| af_sarah | F | C+ | |
| af_alloy | F | C | |
| af_nova | F | C | |
| af_jessica | F | D | |
| af_river | F | D | |
| af_sky | F | C- | Very short training data |
| am_michael | M | C+ | |
| am_fenrir | M | C+ | |
| am_puck | M | C+ | |
| am_echo | M | D | |
| am_eric | M | D | |
| am_liam | M | D | |
| am_onyx | M | D | |
| am_adam | M | F+ | Low quality training data |
| am_santa | M | D- | Very short training data |

### British English (8 voices)

| Voice | Gender | Grade | Notes |
|-------|--------|-------|-------|
| bf_emma | F | B- | Long training data |
| bf_isabella | F | C | |
| bf_alice | F | D | |
| bf_lily | F | D | |
| bm_fable | M | C | Default voice |
| bm_george | M | C | |
| bm_lewis | M | D+ | |
| bm_daniel | M | D | |

### Japanese (5 voices)

| Voice | Gender | Grade |
|-------|--------|-------|
| jf_alpha | F | C+ |
| jf_gongitsune | F | C |
| jf_tebukuro | F | C |
| jf_nezumi | F | C- |
| jm_kumo | M | C- |

### Mandarin Chinese (8 voices)

| Voice | Gender | Grade |
|-------|--------|-------|
| zf_xiaobei | F | D |
| zf_xiaoni | F | D |
| zf_xiaoxiao | F | D |
| zf_xiaoyi | F | D |
| zm_yunjian | M | D |
| zm_yunxi | M | D |
| zm_yunxia | M | D |
| zm_yunyang | M | D |

### Spanish (3 voices)

| Voice | Gender |
|-------|--------|
| ef_dora | F |
| em_alex | M |
| em_santa | M |

### French (1 voice)

| Voice | Gender | Grade |
|-------|--------|-------|
| ff_siwis | F | B- |

### Hindi (4 voices)

| Voice | Gender | Grade |
|-------|--------|-------|
| hf_alpha | F | C |
| hf_beta | F | C |
| hm_omega | M | C |
| hm_psi | M | C |

### Italian (2 voices)

| Voice | Gender | Grade |
|-------|--------|-------|
| if_sara | F | C |
| im_nicola | M | C |

### Brazilian Portuguese (3 voices)

| Voice | Gender |
|-------|--------|
| pf_dora | F |
| pm_alex | M |
| pm_santa | M |

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
# 🚀 Optimized settings: 24k mono MP3, Neural Engine acceleration

# Test with different voices
reader convert --voice af_sarah --file text/sample.txt
reader convert --voice bm_fable --file text/sample.txt
reader convert --voice bf_emma --file text/sample.txt

# List all available voices
reader voices
```

## Strip and Convert Workflow

The recommended workflow is to strip non-content chapters first, then convert:

```bash
reader strip mybook.epub
# → Auto-detects and removes front/back matter (copyright, TOC, index, etc.)
# → Review and refine chapter selection
# → Saves mybook_stripped.epub
# → "Convert to audiobook?" → interactive language/voice/speed dialog
```

Or convert directly with a specific voice:

```bash
reader convert --file mybook.epub --voice af_heart --speed 1.0
```

## G2P Pronunciation Enhancement

Optional phoneme preprocessing for better pronunciation:

```bash
pip install audiobook-reader[g2p-en]
```

When installed, text is converted to IPA phonemes via misaki before Kokoro synthesis. This improves handling of abbreviations ("Dr." → "doctor"), numbers, and homographs. Disable with `--no-g2p`.

**Note:** The `g2p-en` extra installs misaki, num2words, and spacy (but not `phonemizer`, which conflicts with kokoro-onnx's `phonemizer-fork`). Unknown words fall through to Kokoro's internal espeak.

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