# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called "reader" managed with Poetry for dependency management and packaging.

## Development Commands

### Poetry Commands
- `poetry install` - Install all dependencies and create virtual environment
- `poetry add <package>` - Add a new dependency
- `poetry add --group dev <package>` - Add a development dependency
- `poetry remove <package>` - Remove a dependency
- `poetry run <command>` - Run command in Poetry virtual environment
- `poetry shell` - Activate Poetry virtual environment
- `poetry lock` - Update poetry.lock file
- `poetry show` - List installed packages

### Reader CLI Commands

**Quick Start (Neural Engine Optimized):**
- `poetry run python -m reader convert -F file.epub` - Fast Neural Engine conversion (48k mono MP3)
- `poetry run python -m reader convert --debug` - Debug mode with Neural Engine status
- `poetry run python -m reader convert --turbo-mode` - Maximum speed conversion

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

### Phase 3: Advanced Features + Polish (~350MB) ✅ COMPLETED
**Goal**: Professional audiobook production with Neural Engine optimization
- Apple Neural Engine acceleration (CoreML) for M1/M2/M3 Macs
- Dialogue detection and context analysis
- Optimized stream processing with checkpoint resumption  
- 48k mono MP3 encoding for maximum compression
- Thermal management disabled for full Neural Engine performance
- Real-time progress feedback with ETA calculation
- Additional dependencies: spacy, regex

### Architecture Principles
- **Swappable Components**: Abstract base classes for TTS engines, parsers, processors
- **Modular Design**: Easy to upgrade engines without breaking existing code
- **Token-Efficient Development**: ~5K tokens per phase across focused conversations
- **Progressive Enhancement**: Each phase delivers complete, usable software
- never put claude in any git commits