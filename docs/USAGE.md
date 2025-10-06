# Reader CLI Usage Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Place text files in the `text/` folder:**
   ```bash
   cp my-book.epub text/
   cp document.pdf text/
   ```

3. **Convert to audiobook:**
   ```bash
   poetry run reader convert
   ```

4. **Find your audiobook in the `finished/` folder!**

## Commands Reference

### Convert Text to Audiobook

```bash
# Convert all files in text/ folder
poetry run reader convert

# Convert with custom voice
poetry run reader convert --voice "Samantha"

# Convert with custom speed (1.0 = normal, 1.5 = faster, 0.8 = slower)
poetry run reader convert --speed 1.2

# Convert specific file
poetry run reader convert --file path/to/book.epub

# Combine options
poetry run reader convert --voice "Daniel" --speed 1.1 --format wav
```

### Voice Management

```bash
# List all available voices
poetry run reader voices

# See voice details (gender, language)
poetry run reader voices
```

### Configuration

```bash
# View current settings
poetry run reader config

# Set default voice
poetry run reader config --voice "Alex"

# Set default speed
poetry run reader config --speed 1.3

# Set multiple defaults
poetry run reader config --voice "Samantha" --speed 1.1
```

### System Information

```bash
# Show app info and file counts
poetry run reader info
```

## Supported File Formats

### Input Formats
- **`.epub`** - EPUB ebooks (with automatic chapter detection)
- **`.pdf`** - PDF documents (converted page by page)
- **`.txt`** - Plain text files
- **`.md`** - Markdown files (header-based chapters)
- **`.rst`** - ReStructuredText files

### Output Formats
- **`.mp3`** - 48kHz mono, optimized for audiobooks (default)
- **`.wav`** - Uncompressed audio
- **`.m4a`** - Apple-friendly format
- **`.m4b`** - Audiobook format with chapter support

## Examples

### Basic Usage

```bash
# 1. Add a book
echo "Hello world! This is my first audiobook." > text/hello.txt

# 2. Convert it
poetry run reader convert

# 3. Listen to finished/hello_kokoro_am_michael.mp3
```

### Custom Voice Examples

```bash
# Professional male voice
poetry run reader convert --voice "Daniel"

# Clear female voice
poetry run reader convert --voice "Samantha"

# Faster narration
poetry run reader convert --voice "Alex" --speed 1.3
```

### Batch Processing

```bash
# Add multiple books
cp book1.epub book2.pdf story.txt text/

# Convert all at once
poetry run reader convert

# Results:
# - finished/book1_kokoro_am_michael.mp3
# - finished/book2_kokoro_am_michael.mp3
# - finished/story_kokoro_am_michael.mp3
```

### EPUB Example

```bash
# Download a free ebook
curl -o text/alice.epub "https://www.gutenberg.org/ebooks/11.epub.noimages"

# Convert with custom settings
poetry run reader convert --voice "Alice" --speed 1.0

# Result: finished/alice_kokoro_am_michael.mp3
```

### Configuration Workflow

```bash
# First, find your preferred voice
poetry run reader voices | grep -i female

# Set it as default
poetry run reader config --voice "Samantha" --speed 1.1

# Now all conversions use these settings
poetry run reader convert

# Override for specific books
poetry run reader convert --voice "Daniel"  # Uses Daniel, but keeps speed 1.1
```

## Tips & Tricks

### Voice Selection
- **Male voices**: Daniel, Thomas, Alex, Fred
- **Female voices**: Samantha, Alice, Allison, Susan
- **Clear pronunciation**: Samantha, Daniel, Alex
- **Faster speech**: Use `--speed 1.2` to `1.5`
- **Dramatic reading**: Try different voices for characters

### File Organization
```
text/
├── fiction/
│   ├── novel1.epub
│   └── novel2.epub
├── non-fiction/
│   ├── biography.pdf
│   └── manual.txt
└── quick-reads/
    ├── article1.md
    └── article2.txt
```

### Processing Large Files
- Large books are automatically split into chunks
- Each chunk becomes a separate audio file
- Main file contains the first chunk
- Example: `book_part_001.wav`, `book_part_002.wav`, etc.

### Troubleshooting

**No voices available:**
```bash
# Check system voices
poetry run reader voices
```

**File not converting:**
- Check file format is supported
- Ensure file is in `text/` directory
- Try converting specific file: `--file text/yourfile.txt`

**Audio quality:**
- Kokoro TTS provides professional neural voices
- Output: 48kHz mono MP3, optimized for audiobooks
- Adjust `--speed` to find comfortable pace
- Limited storage/processing? Try reader-small package

## Configuration File

Settings are saved to `config/settings.yaml`:

```yaml
tts:
  engine: kokoro          # kokoro or pyttsx3
  voice: am_michael       # Kokoro voice ID
  speed: 1.0
  volume: 1.0
audio:
  format: mp3             # mp3, wav, m4a, m4b
  add_metadata: true
processing:
  chunk_size: 1200
  pause_between_chapters: 1.0
  auto_detect_chapters: true
text_dir: text
finished_dir: finished    # Output directory
```

## Advanced Features

Current features include neural TTS, emotion detection, and character voice mapping.

### Neural TTS with Kokoro (Default)
```bash
# Use Kokoro neural TTS (48+ voices, 8 languages)
poetry run reader convert --engine kokoro

# Explicitly set Kokoro (already default)
poetry run reader convert --engine kokoro
```

### Emotion-Aware Conversion
```bash
# Enable emotion detection
poetry run reader convert --emotion

# With character voice mapping
poetry run reader convert --characters --file text/novel.txt
```

### Progress Visualization
```bash
# ASCII timeseries chart with real-time speed graph (default)
poetry run reader convert --progress-style timeseries

# Simple text progress
poetry run reader convert --progress-style simple

# TQDM progress bars with speed metrics
poetry run reader convert --progress-style tqdm

# Rich formatted display
poetry run reader convert --progress-style rich

# ASCII timeseries chart (real-time speed graph)
poetry run reader convert --progress-style timeseries
```

### Debug Mode
```bash
# See detailed processing info and Neural Engine status
poetry run reader convert --debug --file text/sample.txt
```

### Character Voice Management
```bash
# Add character-to-voice mapping
poetry run reader characters add "Alice" "af_sarah"
poetry run reader characters add "Bob" "am_adam"

# List character mappings
poetry run reader characters list

# Remove character mapping
poetry run reader characters remove "Alice"
```

### Available Kokoro Voices

American English: `af_sarah`, `af_nicole`, `am_michael`, `am_adam`
British English: `bf_emma`, `bf_isabella`, `bm_george`, `bm_lewis`
And 40+ more across Spanish, French, Italian, Portuguese, Japanese, Korean, Chinese

See full list with: `poetry run reader voices`

## Next Steps

For more examples and workflows, see:
- **[EXAMPLES.md](EXAMPLES.md)** - Real-world use cases
- **[PHASE3_FEATURES.md](PHASE3_FEATURES.md)** - Advanced features
- **[KOKORO_SETUP.md](KOKORO_SETUP.md)** - Model setup guide