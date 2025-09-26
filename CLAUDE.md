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
**Main Commands:**
- `poetry run python -m reader info` - Show application information and quick start
- `poetry run python -m reader convert` - Convert text files to audiobooks
- `poetry run python -m reader voices` - List available TTS voices
- `poetry run python -m reader config` - Configure default settings

**Phase 2 Commands (Neural TTS + Emotion Analysis):**
- `poetry run python -m reader convert --engine kokoro --emotion --characters` - Advanced conversion
- `poetry run python -m reader characters add NAME VOICE` - Map character to voice
- `poetry run python -m reader characters list` - Show character mappings
- `poetry run python -m reader blend create NAME SPEC` - Create voice blend (e.g., "voice1:60,voice2:40")
- `poetry run python -m reader blend list` - Show voice blends

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

### Phase 3: Advanced Features + Polish (~350MB)
**Goal**: Professional audiobook production
- Dialogue detection and context analysis
- Chapter metadata and M4B export
- Multiple audio formats (MP3, M4A, M4B)
- Voice preview and batch processing
- Additional dependencies: spacy, regex

### Architecture Principles
- **Swappable Components**: Abstract base classes for TTS engines, parsers, processors
- **Modular Design**: Easy to upgrade engines without breaking existing code
- **Token-Efficient Development**: ~5K tokens per phase across focused conversations
- **Progressive Enhancement**: Each phase delivers complete, usable software