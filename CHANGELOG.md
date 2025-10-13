# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.6] - 2025-10-13

### Added
- References to [convertext](https://pypi.org/project/convertext/) package for additional format support
- Clear workflow for converting DOCX, MOBI, HTML, and other formats to supported inputs
- Examples in README and documentation showing convertext usage

### Changed
- Updated PyPI description to mention convertext for additional format support

## [0.1.5] - 2025-10-13

### Added
- **Programmatic Python API** for Jupyter notebooks and scripts
  - `Reader` class for object-oriented usage
  - `convert()` convenience function for simple conversions
  - `list_voices()` function to query available voices
  - Comprehensive API documentation in `docs/API.md`
- Python API quick start section in README

### Fixed
- PyPI badge links now correctly point to `audiobook-reader` package

### Changed
- Performance claim updated to "up to 8x faster than real-time" (from 6x)

## [0.1.4] - 2025-10-13

### Fixed
- Automatic chunk splitting for texts exceeding Kokoro's 510 phoneme limit (primarily affects non-English text like Greek, Cyrillic, Arabic)
- Checkpoint resume path comparison now correctly handles relative vs absolute paths
- Kokoro library warnings suppressed in non-debug mode
- Character voices now only enabled when explicitly using --characters flag

### Added
- Enhanced debug logging throughout checkpoint and progress systems (--debug flag)
- Automatic sentence-level splitting for chunks with high phoneme counts
- Graceful handling of academic texts with mixed languages and special characters

## [0.1.3] - 2025-10-11

### Changed
- Updated documentation interlinking

### Added
- MP3 quality/bitrate configuration parameter
- Local model storage option with --local flag

## [0.1.2] - 2025-10-09

### Fixed
- Documentation links now point to GitHub (were broken on PyPI)

## [0.1.1] - 2025-10-09

### Changed
- Updated project description

## [0.1.0] - 2025-01-09

### Added
- **Neural Engine Optimization**: Apple M1/M2/M3/M4 acceleration via CoreML for ultra-fast TTS processing
- **Kokoro TTS Integration**: 48 high-quality voices across 8 languages
- **Character Voice Mapping**: Automatic dialogue detection and character-specific voice assignment
- **Emotion Analysis**: VADER sentiment analysis for dynamic prosody and emotional inflection
- **Multiple Input Formats**: Support for EPUB, PDF, TXT, and reStructuredText files
- **Progress Visualization**: 4 progress styles (simple, tqdm, rich, timeseries) with real-time metrics
- **Checkpoint Recovery**: Resume interrupted conversions from last successful chunk
- **Professional Audio Output**: 48kHz mono MP3 encoding with FFmpeg batch conversion
- **Smart Chunking**: 400-character chunks optimized for Kokoro TTS quality
- **Voice Management**: CLI commands for listing voices and mapping characters
- **Configuration System**: Persistent settings with processing level management
- **First-Run Setup**: Automatic directory creation and environment validation
- **FFmpeg Integration**: Batch audio assembly with streaming architecture
- **Cross-Platform Support**: macOS (Neural Engine), Linux/Windows (CPU), GPU acceleration options

### Technical Details
- Default voice: `am_michael` (American English male)
- Audio format: 48kHz mono MP3 (optimized for audiobook distribution)
- Emotion detection: VADER sentiment analysis with SSML prosody mapping
- Architecture: Streaming NeuralProcessor with memory-efficient chunk processing
- Dependencies: kokoro-onnx, onnxruntime, vaderSentiment, ebooklib, PyPDF2, pydub

### Commands
- `reader convert` - Convert text files to audiobooks
- `reader voices` - List available TTS voices
- `reader characters` - Manage character voice mappings
- `reader config` - Configure default settings
- `reader info` - Show application information

[0.1.2]: https://github.com/danielcorsano/reader/releases/tag/v0.1.2
[0.1.1]: https://github.com/danielcorsano/reader/releases/tag/v0.1.1
[0.1.0]: https://github.com/danielcorsano/reader/releases/tag/v0.1.0
