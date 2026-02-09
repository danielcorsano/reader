# Changelog

All notable user-facing changes to this project will be documented in this file.

## [0.3.0] - 2026-02-09

### Added
- `reader strip` command — interactive chapter stripping with auto-detection of non-content (copyright, index, bibliography, etc.)
- Auto-strip with 5-signal content classifier: title keywords, EPUB metadata, content patterns, prose density, relative chapter length
- Manual refinement after auto-strip for fine-tuning
- Tiered chapter detection for PDFs and plain text (known headings, isolated titles, ALL CAPS fallback)

## [0.1.8] - 2025-10-20

### Added
- `reader strip` command for interactive chapter removal with auto-detection
- Real section detection in PDFs (replaces page numbers)
- Spoiler-protected end preview (hidden by default)

## [0.1.7] - 2025-10-18

### Added
- `--output-dir` option: `downloads`, `same` (next to source), or custom path

### Changed
- Working files now use `/tmp/audiobook-reader-{session}/` with auto-cleanup
- Config moved to `~/.config/audiobook-reader/` (XDG standard)
- Default output is now `~/Downloads/`

## [0.1.6] - 2025-10-13

### Added
- [convertext](https://pypi.org/project/convertext/) integration for DOCX, MOBI, HTML format support

## [0.1.5] - 2025-10-13

### Added
- **Programmatic Python API** — `Reader` class, `convert()`, `list_voices()`

## [0.1.3] - 2025-10-11

### Added
- MP3 quality/bitrate configuration parameter
- Local model storage with `--local` flag

## [0.1.0] - 2025-01-09

### Added
- **Neural Engine Optimization**: Apple M1/M2/M3/M4 acceleration via CoreML
- **Kokoro TTS Integration**: 54 high-quality voices across 9 languages
- **Character Voice Mapping**: Dialogue detection and character-specific voices
- **Emotion Analysis**: VADER sentiment for dynamic prosody
- **Multiple Input Formats**: EPUB, PDF, TXT, reStructuredText
- **Progress Visualization**: 4 styles (simple, tqdm, rich, timeseries)
- **Checkpoint Recovery**: Resume interrupted conversions
- **48kHz mono MP3** encoding with FFmpeg batch conversion

[0.3.0]: https://github.com/danielcorsano/reader/releases/tag/v0.3.0
[0.1.8]: https://github.com/danielcorsano/reader/releases/tag/v0.1.8
[0.1.7]: https://github.com/danielcorsano/reader/releases/tag/v0.1.7
[0.1.6]: https://github.com/danielcorsano/reader/releases/tag/v0.1.6
[0.1.5]: https://github.com/danielcorsano/reader/releases/tag/v0.1.5
[0.1.3]: https://github.com/danielcorsano/reader/releases/tag/v0.1.3
[0.1.0]: https://github.com/danielcorsano/reader/releases/tag/v0.1.0
