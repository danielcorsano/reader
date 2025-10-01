# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called "reader" managed with Poetry for dependency management and packaging.

## Development Commands

**IMPORTANT: This project uses Poetry for dependency management. Always use `poetry add/remove`, never use `pip install` directly.**

### Poetry Commands
- `poetry install` - Install all dependencies and create virtual environment
- `poetry install --extras "nlp progress-full"` - Install with optional extras
- `poetry add <package>` - Add a new dependency (use this, NOT pip install)
- `poetry add <package> --optional` - Add as optional dependency
- `poetry add --group dev <package>` - Add a development dependency
- `poetry remove <package>` - Remove a dependency
- `poetry run <command>` - Run command in Poetry virtual environment
- `poetry shell` - Activate Poetry virtual environment
- `poetry lock` - Update poetry.lock file
- `poetry show` - List installed packages

### Optional Extras
- `nlp` - Advanced NLP with spacy (dialogue detection)
- `progress-full` - All progress visualizations (plotext, tqdm, rich)
- `progress-timeseries` - ASCII timeseries charts (plotext)
- `progress-tqdm` - TQDM progress bars
- `progress-rich` - Rich enhanced displays
- `monitoring` - System monitoring (psutil)
- `phase1` - pyttsx3 system TTS
- `all` - All optional features

### GPU Acceleration Setup
```bash
# For NVIDIA GPU (Windows/Linux)
poetry remove onnxruntime
poetry add onnxruntime-gpu

# For AMD/Intel GPU (Windows via DirectML)
poetry remove onnxruntime
poetry add onnxruntime-directml

# Apple Silicon uses CoreML by default (no changes needed)
```

### Reader CLI Commands

**Quick Start (Neural Engine Optimized):**
- `poetry run python -m reader convert -F file.epub` - Fast Neural Engine conversion (48k mono MP3)
- `poetry run python -m reader convert --debug` - Debug mode with Neural Engine status
- Features: Emotion analysis, character voices, dialogue detection, checkpoint resumption

**Configuration:**
- `poetry run python -m reader config` - Configure default settings  
- `poetry run python -m reader voices` - List available TTS voices
- `poetry run python -m reader info` - Show application information

**Advanced Options:**
- `poetry run python -m reader convert -v voice_name` - Use specific voice
- `poetry run python -m reader convert -s 1.2` - Adjust speech speed  
- `poetry run python -m reader convert -f wav` - Different output format
- `poetry run python -m reader convert --no-emotion` - Disable emotion analysis
- `poetry run python -m reader convert --batch-mode` - Enable checkpointing

**Progress Display Options:**
- `poetry run python -m reader convert --progress-style simple` - Default text progress (default)
- `poetry run python -m reader convert --progress-style tqdm` - TQDM progress bar with speed metrics
- `poetry run python -m reader convert --progress-style rich` - Rich enhanced display with beautiful formatting  
- `poetry run python -m reader convert --progress-style timeseries` - Real-time ASCII charts of processing speed

**Optional Progress Dependencies:**
- `poetry add tqdm` - For enhanced progress bars with ETA and speed metrics
- `poetry add rich` - For beautiful terminal formatting and enhanced progress displays
- `poetry add plotext` - For ASCII timeseries charts and real-time speed visualization
- All progress styles gracefully fall back to simple display if dependencies are missing

**Character Management:**
- `poetry run python -m reader characters add NAME VOICE` - Map character to voice
- `poetry run python -m reader characters list` - Show character mappings

### Testing and Code Quality
- `poetry run pytest` - Run tests
- `poetry run black .` - Format code
- `poetry run flake8` - Lint code

## Architecture and Structure

- Dependencies managed via `pyproject.toml`
- Virtual environment managed by Poetry
- Development dependencies isolated in dev group
- Source code in `reader/` package directory

## Getting Started

1. Install dependencies: `poetry install`
2. Add new dependencies: `poetry add <package>`
3. Run commands in environment: `poetry run <command>`
4. Always commit `poetry.lock` for reproducible builds

## Important Notes

- Never manually edit `poetry.lock` - let Poetry manage it
- Use `poetry add` instead of pip install
- Prefer virtual environment managed by Poetry over manual venv creation
- Specify version constraints when adding dependencies for stability

## Project Plan: 3-Phase Audiobook CLI Development

### Phase 1: Basic CLI Foundation (~50MB)
**Goal**: Working audiobook generator with pyttsx3
- Basic CLI with pyttsx3 TTS engine
- EPUB/PDF/TXT text parsing
- Modular architecture for easy component swapping
- Configuration management
- Dependencies: pyttsx3, ebooklib, PyPDF2, pydub, click, pyyaml

### Phase 2: Enhanced TTS + Smart Acting (~300MB)
**Goal**: High-quality voices + emotion-aware narration
- Kokoro TTS engine (48 voices, 8 languages)
- Voice blending and character mapping
- VADER emotion detection → SSML prosody
- Smart acting rules (punctuation, context keywords)
- Additional dependencies: kokoro-onnx, onnxruntime, vaderSentiment

### Current Architecture ✅ COMPLETED
**Professional audiobook production with Neural Engine optimization**
- Apple Neural Engine acceleration (CoreML) for M1/M2/M3 Macs
- NeuralProcessor with streaming audio assembly
- Emotion analysis, character voice mapping, dialogue detection
- Optimized 400-character chunking aligned with Kokoro
- 48k mono MP3 encoding with FFmpeg batch conversion
- Real-time progress visualization (4 styles: simple, tqdm, rich, timeseries)
- Checkpoint resumption for interrupted conversions
- Default voice: am_michael

### Architecture Principles
- **Swappable Components**: Abstract base classes for TTS engines and parsers
- **Modular Design**: Easy to add new engines or file formats
- **Streaming Architecture**: Memory-efficient processing for large books