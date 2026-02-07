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

# Disable text cleanup (keep broken words, metadata chapters)
reader convert --file book.epub --no-clean-text

# Combine options
reader convert --voice "Daniel" --speed 1.1 --format wav
```

### Text Cleanup (Automatic)

**Enabled by default** to improve audio quality:

```bash
# Standard conversion with text cleanup (default)
reader convert --file book.epub

# Disable cleanup to keep everything
reader convert --file book.epub --no-clean-text
```

**What Gets Cleaned:**
1. **Broken words fixed**: `"exam-\nple"` → `"example"` (common in PDFs)
2. **Metadata removed**: ISBN lines, book catalogs
3. **Non-narrative chapters skipped**:
   - Table of Contents
   - Bibliography / References
   - Index
   - About the Author / Publisher
   - Acknowledgments
   - "Books by [Author]" / "Other Works"
4. **Narrative boundaries extracted**: 5-signal classifier removes all front/back matter (including short stubs like title pages)

**Benefits:**
- ✅ No pronunciation errors from broken words
- ✅ No metadata narration
- ✅ 10-20% faster processing on academic books

**When to disable:** Use `--no-clean-text` if you need verbatim conversion including all metadata.

### Strip Chapters from Documents

Interactively remove unwanted sections before converting:

```bash
# Strip chapters from any supported format
reader strip book.epub
reader strip document.pdf
reader strip textbook.txt

# Flow:
# 1. Tiered chapter detection:
#    - Marked chapters (EPUB h1-h6, existing structure)
#    - Heading detection (known sections, isolated title lines)
#    - Formatting fallback (ALL CAPS lines, spacing patterns)
# 2. Auto-strip with 5-signal content classifier
#    (title keywords, EPUB metadata, content patterns, prose density, relative length)
#    - Front-matter bias (copyright/title pages detected more aggressively)
#    - Conservative back-stripping (harder to accidentally cut ending)
#    - Spoiler-protected end preview
# 3. Manual refinement:
#    s 0, 6-8  → Strip chapters 0, 6, 7, 8 (keep the rest)
#    k 1-5     → Keep chapters 1-5 only (strip the rest)
# 4. Saves stripped file, offers conversion
```

**Output formats:**
- EPUB → `_stripped.epub` (preserves structure, CSS, images)
- TXT/MD/RST → `_stripped.txt`
- PDF → `_stripped.txt` (extracts to text)

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
- **`.epub`** - EPUB ebooks (structural markup chapter detection)
- **`.pdf`** - PDF documents (heading detection → formatting fallback)
- **`.txt`** - Plain text files (heading detection → formatting fallback)
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

### Strip and Convert Example

```bash
# Strip a philosophy textbook to just the main chapters
reader strip "Spinoza - Ethics.epub"
# Output:
#   0: Title Page
#      "THE ESSENTIAL SPINOZA..."
#   1: Editor's Introduction
#      "This volume brings together..."
#   2: Part I - On God
#      "By substance I understand..."
#   ...
# Strip chapters? [y/n]: y
# Enter selection: k 2-8
# Keeping 7 of 12 chapters...
# Saved: Spinoza - Ethics_stripped.epub
# Convert to audiobook? [y/n]: y
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

## Multi-Layer Configuration System

Reader uses a hierarchical configuration system that lets you set defaults at different levels:

### Configuration Hierarchy (priority: low → high)

1. **Defaults** - Built-in sensible defaults
2. **User config** - `~/.config/audiobook-reader/config.yaml` (your personal defaults)
3. **Project config** - `.reader.yaml` or `audiobook-reader.yaml` (per-project overrides)
4. **CLI arguments** - Temporary overrides for single conversion

Each layer **merges** with the previous (doesn't replace entirely), so you only need to specify what you want to override.

### User Config

Your personal defaults for all audiobook conversions:

**Location:** `~/.config/audiobook-reader/config.yaml`

```yaml
tts:
  engine: kokoro
  voice: af_sarah         # Your preferred voice
  speed: 1.2              # Your preferred speed
  volume: 1.0
audio:
  format: m4b             # Audiobook format with chapters
  add_metadata: true
processing:
  chunk_size: 400
  pause_between_chapters: 1.0
  auto_detect_chapters: true
output_dir: /audiobooks   # Your audiobook library
```

### Project Config

Override settings for specific directories/projects. Reader searches upward from your file's directory to find the nearest config.

**Location:** `.reader.yaml` or `audiobook-reader.yaml` (in any parent directory)

**Example - Fiction Books:**
```yaml
# ~/books/fiction/.reader.yaml
tts:
  voice: am_michael       # Dramatic narrator voice
  speed: 1.0              # Normal speed for immersion
processing:
  character_voices: true  # Enable character-specific voices
```

**Example - Non-Fiction:**
```yaml
# ~/books/non-fiction/.reader.yaml
tts:
  voice: af_nicole        # Clear, professional voice
  speed: 1.3              # Faster for educational content
audio:
  format: mp3             # Standard format for lectures
```

### How Merging Works

**Example:** You have both user and project configs:

```yaml
# User config: ~/.config/audiobook-reader/config.yaml
tts:
  voice: af_sarah
  speed: 1.2
audio:
  format: m4b
output_dir: /audiobooks
```

```yaml
# Project config: ~/books/fiction/.reader.yaml
tts:
  voice: am_michael       # Override voice only
processing:
  character_voices: true  # Add new setting
```

**Result when converting `~/books/fiction/novel.epub`:**
- `voice`: `am_michael` (from project config)
- `speed`: `1.2` (from user config - inherited!)
- `format`: `m4b` (from user config - inherited!)
- `character_voices`: `true` (from project config)
- `output_dir`: `/audiobooks` (from user config - inherited!)

**Only the voice changed!** All other user settings are preserved.

### Configuration Use Cases

**1. Personal Defaults**
```bash
# Set once, applies to all conversions
reader config --voice af_sarah --speed 1.2 --format m4b
```

**2. Per-Project Override**
```bash
# Create project config for all books in directory
cd ~/books/fiction
cat > .reader.yaml << EOF
tts:
  voice: am_michael
processing:
  character_voices: true
EOF

# Now all conversions in fiction/ use character voices automatically
reader convert --file novel.epub
```

**3. Team Collaboration**
```bash
# Check project config into git for team
cd my-audiobook-project
cat > .reader.yaml << EOF
tts:
  voice: bf_emma
  speed: 1.0
audio:
  format: m4b
EOF

git add .reader.yaml
git commit -m "Add audiobook config"
# Team members inherit these settings automatically!
```

**4. Testing Voice Combinations**
```bash
# User config has your defaults
# Create test directory with different voice
mkdir voice-tests
cd voice-tests
echo "tts:\n  voice: am_adam" > .reader.yaml

# Convert sample to test - inherits your other settings
reader convert --file ../sample.txt
```

**5. Config Inheritance**
```bash
# Parent directory config
~/books/.reader.yaml:
  audio:
    format: m4b
  output_dir: /audiobooks

# Child directory adds character voices
~/books/fiction/.reader.yaml:
  processing:
    character_voices: true

# Files in ~/books/fiction/ get BOTH configs merged!
```

## File Locations

Reader uses system-standard directories:

**Configuration Files:**
- `~/.config/audiobook-reader/config.yaml` - User-level defaults (all projects)
- `.reader.yaml` or `audiobook-reader.yaml` - Project-level overrides (searches upward)

**Temporary Files:**
- `/tmp/audiobook-reader-{session}/` - Working files (auto-cleaned on exit)

**Persistent Data:**
- `~/.cache/audiobook-reader/models/` - TTS models (~310MB)
- `~/.config/audiobook-reader/` - User configuration and character mappings

**Output Files:**
- `~/Downloads/` (default, configurable with `output_dir`)
- `--output-dir same` - Next to source file
- `--output-dir /custom` - Custom path

## Advanced Features

Current features include neural TTS, dialogue detection, and character voice mapping.

### Neural TTS with Kokoro (Default)
```bash
# Use Kokoro neural TTS (54 voices, 9 languages)
reader convert --engine kokoro

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

**54 voices across 9 languages:**
- **American English** (20): af_heart, af_alloy, af_aoede, af_bella, af_jessica, af_kore, af_nicole, af_nova, af_river, af_sarah, af_sky, am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck, am_santa
- **British English** (8): bf_alice, bf_emma, bf_isabella, bf_lily, bm_daniel, bm_fable, bm_george, bm_lewis
- **Japanese** (5): jf_alpha, jf_gongitsune, jf_nezumi, jf_tebukuro, jm_kumo
- **Mandarin Chinese** (8): zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zf_xiaoyi, zm_yunjian, zm_yunxi, zm_yunxia, zm_yunyang
- **Spanish** (3): ef_dora, em_alex, em_santa
- **French** (1): ff_siwis
- **Hindi** (4): hf_alpha, hf_beta, hm_omega, hm_psi
- **Italian** (2): if_sara, im_nicola
- **Brazilian Portuguese** (3): pf_dora, pm_alex, pm_santa

See full list with: `reader voices`

## Next Steps

For more examples and workflows, see:
- **[EXAMPLES.md](EXAMPLES.md)** - Real-world use cases
- **[ADVANCED_FEATURES.md](ADVANCED_FEATURES.md)** - Advanced features
- **[KOKORO_SETUP.md](KOKORO_SETUP.md)** - Model setup guide