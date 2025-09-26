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

4. **Find your audiobook in the `audio/` folder!**

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
- **`.wav`** - Uncompressed audio (Phase 1 only)
- Future phases will add: MP3, M4A, M4B with metadata

## Examples

### Basic Usage

```bash
# 1. Add a book
echo "Hello world! This is my first audiobook." > text/hello.txt

# 2. Convert it
poetry run reader convert

# 3. Listen to audio/hello.wav
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
# - audio/book1.wav
# - audio/book2.wav
# - audio/story.wav
```

### EPUB Example

```bash
# Download a free ebook
curl -o text/alice.epub "https://www.gutenberg.org/ebooks/11.epub.noimages"

# Convert with custom settings
poetry run reader convert --voice "Alice" --speed 1.0

# Result: audio/Alice's Adventures in Wonderland.wav
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
- Phase 1 uses system TTS (basic quality)
- Phase 2+ will add neural TTS for professional quality
- Adjust `--speed` to find comfortable pace

## Configuration File

Settings are saved to `config/settings.yaml`:

```yaml
tts:
  engine: pyttsx3
  voice: "Samantha"
  speed: 1.1
  volume: 1.0
audio:
  format: wav
  add_metadata: false
processing:
  chunk_size: 1000
  pause_between_chapters: 1.0
  auto_detect_chapters: true
text_dir: text
audio_dir: audio
```

## Phase 2: Advanced Features

Phase 2 adds neural TTS, emotion detection, and character voice mapping.

### Neural TTS with Kokoro
```bash
# Use Kokoro neural TTS (48+ voices, 8 languages)
poetry run reader convert --engine kokoro

# Combine with emotion analysis
poetry run reader convert --engine kokoro --emotion
```

### Emotion-Aware Conversion
```bash
# Enable emotion detection and smart acting
poetry run reader convert --emotion

# Full Phase 2 features
poetry run reader convert --engine kokoro --emotion --characters
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

### Voice Blending
```bash
# Create custom voice blend (weights as percentages)
poetry run reader blend create "MyBlend" "af_sarah:60,af_sky:40"

# List voice blends
poetry run reader blend list

# Remove voice blend
poetry run reader blend remove "MyBlend"
```

## Next Steps

- **Phase 3**: Professional audiobook formats (MP3, M4B), batch processing, advanced dialogue detection

For advanced features and development, see the main README.md.