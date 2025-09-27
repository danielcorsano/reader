# Kokoro TTS Setup Requirements

## Current Status
- Kokoro ONNX library is installed via Poetry
- Engine implementation is in `reader/engines/kokoro_engine.py`
- Model files need to be downloaded (large files - 310MB each)

## Required Model Files
Download these files to `models/kokoro/`:

```bash
mkdir -p models/kokoro
cd models/kokoro

# Download model files (310MB each)
curl -L -o kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

## Required Code Fix
Update `reader/engines/kokoro_engine.py` line 61:

```python
# Current (broken):
self.kokoro = Kokoro(model_path=None, voices_path=None)

# Fix to:
model_path = Path(__file__).parent.parent.parent / "models" / "kokoro" / "kokoro-v1.0.onnx"
voices_path = Path(__file__).parent.parent.parent / "models" / "kokoro" / "voices-v1.0.bin"
self.kokoro = Kokoro(str(model_path), str(voices_path))
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

## Testing Commands
After setup:
```bash
# Test Phase 2 with emotion analysis
poetry run python -m reader convert --processing-level phase2 --engine kokoro --voice "af_sarah" --speed 0.9 --emotion --file text/test_story.txt

# Test Phase 3 with all features
poetry run python -m reader convert --processing-level phase3 --engine kokoro --voice "af_sarah" --speed 0.9 --emotion --characters --file text/test_story.txt
```