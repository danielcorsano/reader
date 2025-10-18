# Reader CLI Usage Guide

## Quick Start

1. **Install package:**
   ```bash
   pip install audiobook-reader
   ```

2. **Convert any text file directly:**
   ```bash
   reader convert --file my-book.epub
   ```

3. **Find your audiobook in `~/Downloads/`!**

## Output Directory Options

Control where your audiobooks are saved:

```bash
# Default: ~/Downloads/
reader convert --file book.epub

# Next to source file
reader convert --file book.epub --output-dir same

# Custom location
reader convert --file book.epub --output-dir /path/to/audiobooks

# Set default in config
reader config --output-dir /path/to/audiobooks
```

## Commands Reference

### Convert Text to Audiobook

```bash
# Convert all files in text/ folder
reader convert

# Convert with custom voice
reader convert --voice "Samantha"

# Convert with custom speed (1.0 = normal, 1.5 = faster, 0.8 = slower)
reader convert --speed 1.2

# Convert specific file
reader convert --file path/to/book.epub

# Combine options
reader convert --voice "Daniel" --speed 1.1 --format wav
```

### Voice Management

```bash
# List all available voices
reader voices

# See voice details (gender, language)
reader voices
```

### Configuration

```bash
# View current settings
reader config

# Set default voice
reader config --voice "Alex"

# Set default speed
reader config --speed 1.3

# Set multiple defaults
reader config --voice "Samantha" --speed 1.1
```

### System Information

```bash
# Show app info and file counts
reader info
```

## Supported File Formats

### Input Formats
- **`.epub`** - EPUB ebooks (with automatic chapter detection)
- **`.pdf`** - PDF documents (converted page by page)
- **`.txt`** - Plain text files
- **`.md`** - Markdown files (header-based chapters)
- **`.rst`** - ReStructuredText files

**Need to convert other formats?** Use [convertext](https://pypi.org/project/convertext/) to convert DOCX, ODT, MOBI, HTML, and other document formats to supported formats.

### Output Formats
- **`.mp3`** - 48kHz mono, 48kbps VBR (optimized for speech, default)
- **`.wav`** - 48kHz mono PCM, uncompressed (highest quality)
- **`.m4a`** - 48kHz AAC 128kbps (Apple ecosystem)
- **`.m4b`** - 48kHz AAC 128kbps with chapter markers (professional audiobook format)

## Examples

### Basic Usage

```bash
# 1. Create a text file
echo "Hello world! This is my first audiobook." > hello.txt

# 2. Convert it
reader convert --file hello.txt

# 3. Listen to ~/Downloads/hello_kokoro_am_michael.mp3
```

### Custom Voice Examples

```bash
# Professional male voice
reader convert --voice "Daniel"

# Clear female voice
reader convert --voice "Samantha"

# Faster narration
reader convert --voice "Alex" --speed 1.3
```

### Batch Processing

```bash
# Convert multiple files to same location
reader convert --file book1.epub --output-dir /audiobooks
reader convert --file book2.pdf --output-dir /audiobooks
reader convert --file story.txt --output-dir /audiobooks

# Results:
# - /audiobooks/book1_kokoro_am_michael.mp3
# - /audiobooks/book2_kokoro_am_michael.mp3
# - /audiobooks/story_kokoro_am_michael.mp3
```

### EPUB Example

```bash
# Download a free ebook
curl -o text/alice.epub "https://www.gutenberg.org/ebooks/11.epub.noimages"

# Convert with custom settings
reader convert --voice "Alice" --speed 1.0

# Result: finished/alice_kokoro_am_michael.mp3
```

### Configuration Workflow

```bash
# First, find your preferred voice
reader voices | grep -i female

# Set it as default
reader config --voice "Samantha" --speed 1.1

# Now all conversions use these settings
reader convert

# Override for specific books
reader convert --voice "Daniel"  # Uses Daniel, but keeps speed 1.1
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
reader voices
```

**File not converting:**
- Check file format is supported
- Ensure file is in `text/` directory
- Try converting specific file: `--file text/yourfile.txt`

**Audio quality:**
- Kokoro TTS provides professional neural voices
- Output: 48kHz mono MP3, optimized for audiobooks
- Adjust `--speed` to find comfortable pace

## Configuration File

Settings are saved to `~/.config/audiobook-reader/settings.yaml`:

```yaml
tts:
  engine: kokoro          # TTS engine (kokoro)
  voice: am_michael       # Kokoro voice ID
  speed: 1.0
  volume: 1.0
audio:
  format: mp3             # mp3, wav, m4a, m4b
  add_metadata: true
processing:
  chunk_size: 400         # Optimized for Kokoro
  pause_between_chapters: 1.0
  auto_detect_chapters: true
output_dir: downloads     # "downloads", "same", or custom path
```

## File Locations

Reader uses system-standard directories:

**Temporary Files:**
- `/tmp/audiobook-reader-{session}/` - Working files (auto-cleaned on exit)

**Persistent Data:**
- `~/.cache/audiobook-reader/models/` - TTS models (~310MB)
- `~/.config/audiobook-reader/` - Configuration and character mappings

**Output Files:**
- `~/Downloads/` (default, configurable with `output_dir`)
- `--output-dir same` - Next to source file
- `--output-dir /custom` - Custom path

## Advanced Features

Current features include neural TTS, emotion detection, and character voice mapping.

### Neural TTS with Kokoro (Default)
```bash
# Use Kokoro neural TTS (48+ voices, 8 languages)
reader convert --engine kokoro

# Explicitly set Kokoro (already default)
reader convert --engine kokoro
```

### Emotion-Aware Conversion
```bash
# Enable emotion detection
reader convert --emotion

# With character voice mapping
reader convert --characters --file text/novel.txt
```

### Progress Visualization
```bash
# ASCII timeseries chart with real-time speed graph (default)
reader convert --progress-style timeseries

# Simple text progress
reader convert --progress-style simple

# TQDM progress bars with speed metrics
reader convert --progress-style tqdm

# Rich formatted display
reader convert --progress-style rich

# ASCII timeseries chart (real-time speed graph)
reader convert --progress-style timeseries
```

### Debug Mode
```bash
# See detailed processing info and Neural Engine status
reader convert --debug --file text/sample.txt
```

### Character Voice Management
```bash
# Add character-to-voice mapping
reader characters add "Alice" "af_sarah"
reader characters add "Bob" "am_adam"

# List character mappings
reader characters list

# Remove character mapping
reader characters remove "Alice"
```

### Available Kokoro Voices

American English: `af_sarah`, `af_nicole`, `am_michael`, `am_adam`
British English: `bf_emma`, `bf_isabella`, `bm_george`, `bm_lewis`
And 40+ more across Spanish, French, Italian, Portuguese, Japanese, Korean, Chinese

See full list with: `reader voices`

## Next Steps

For more examples and workflows, see:
- **[EXAMPLES.md](EXAMPLES.md)** - Real-world use cases
- **[PHASE3_FEATURES.md](PHASE3_FEATURES.md)** - Advanced features
- **[KOKORO_SETUP.md](KOKORO_SETUP.md)** - Model setup guide