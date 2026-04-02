# Reader CLI Usage Guide

## Quick Start

1. **Install package:**
   ```bash
   pip install audiobook-reader
   ```

2. **Strip and convert (recommended):**
   ```bash
   reader strip my-book.epub
   # Removes non-content, then guides you through language/voice/speed selection
   ```

3. **Or convert directly (interactive dialog selects language, voice, speed):**
   ```bash
   reader convert --file my-book.epub
   ```

4. **Find your audiobook in `~/Downloads/`!**

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
# Convert a file
reader convert --file book.epub

# Convert with custom voice
reader convert --voice af_sarah

# Convert with custom speed (1.0 = normal, 1.5 = faster, 0.8 = slower)
reader convert --speed 1.2

# Convert specific file
reader convert --file path/to/book.epub

# Disable text cleanup (keep broken words, metadata chapters)
reader convert --file book.epub --no-clean-text

# Combine options
reader convert --voice bm_george --speed 1.0 --format wav
```

### G2P Pronunciation Enhancement (Optional)

Install the G2P extra for improved pronunciation of abbreviations, numbers, and unusual words:

```bash
pip install audiobook-reader[g2p-en]
```

G2P (grapheme-to-phoneme) converts text to IPA phonemes via [misaki](https://github.com/hexgrad/misaki) before synthesis. When installed, it activates automatically. Disable with `--no-g2p`.

```bash
# Convert with G2P enabled (automatic when installed)
reader convert --file book.epub

# Disable G2P for a specific conversion
reader convert --file book.epub --no-g2p
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
# 5. Interactive dialog: choose language → voice → speed
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
reader config --voice am_adam

# Set default speed
reader config --speed 1.3

# Set multiple defaults
reader config --voice af_sarah --speed 1.0
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
- **`.mp3`** - 24kHz mono, 48kbps CBR (optimized for speech, default)
- **`.wav`** - 24kHz mono PCM, uncompressed (highest quality)
- **`.m4a`** - AAC 128kbps (Apple ecosystem)
- **`.m4b`** - AAC 128kbps with chapter markers (professional audiobook format)

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
reader convert --voice bm_george

# Clear female voice
reader convert --voice af_sarah

# Faster narration
reader convert --voice am_adam --speed 1.3
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
# → Select language, voice, and speed interactively
```

### EPUB Example

```bash
# Download a free ebook
curl -o text/alice.epub "https://www.gutenberg.org/ebooks/11.epub.noimages"

# Convert with custom settings
reader convert --voice bf_alice --speed 1.0

# Result: ~/Downloads/alice_bf_alice_sp1p1.mp3
```

### Configuration Workflow

```bash
# First, find your preferred voice
reader voices | grep -i female

# Set it as default
reader config --voice af_sarah --speed 1.0

# Now all conversions use these settings
reader convert

# Override for specific books
reader convert --voice bm_george  # Uses Daniel, but keeps speed 1.0
```

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

**54 voices across 9 languages.** Grades from [Kokoro-82M VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) reflect training data quality and quantity. Voices perform best on 100-200 tokens; may rush on 400+.

**American English** (20 voices):

| Voice | Gender | Grade | Notes |
|-------|--------|-------|-------|
| af_heart | F | A | Best overall quality |
| af_bella | F | A- | High quality, long training data |
| af_nicole | F | B- | Long training data |
| af_aoede | F | C+ | |
| af_kore | F | C+ | |
| af_sarah | F | C+ | |
| af_alloy | F | C | |
| af_nova | F | C | |
| af_jessica | F | D | |
| af_river | F | D | |
| af_sky | F | C- | Very short training data |
| am_michael | M | C+ | Default voice |
| am_fenrir | M | C+ | |
| am_puck | M | C+ | |
| am_echo | M | D | |
| am_eric | M | D | |
| am_liam | M | D | |
| am_onyx | M | D | |
| am_adam | M | F+ | Low quality training data |
| am_santa | M | D- | Very short training data |

**British English** (8): bf_emma (F, B-), bf_isabella (F, C), bf_alice (F, D), bf_lily (F, D), bm_fable (M, C), bm_george (M, C), bm_lewis (M, D+), bm_daniel (M, D)

**Japanese** (5): jf_alpha (F, C+), jf_gongitsune (F, C), jf_tebukuro (F, C), jf_nezumi (F, C-), jm_kumo (M, C-)

**Mandarin Chinese** (8): zf_xiaobei (F, D), zf_xiaoni (F, D), zf_xiaoxiao (F, D), zf_xiaoyi (F, D), zm_yunjian (M, D), zm_yunxi (M, D), zm_yunxia (M, D), zm_yunyang (M, D)

**Spanish** (3): ef_dora (F), em_alex (M), em_santa (M)

**French** (1): ff_siwis (F, B-)

**Hindi** (4): hf_alpha (F, C), hf_beta (F, C), hm_omega (M, C), hm_psi (M, C)

**Italian** (2): if_sara (F, C), im_nicola (M, C)

**Brazilian Portuguese** (3): pf_dora (F), pm_alex (M), pm_santa (M)

See full list with: `reader voices`

## Next Steps

For more examples and workflows, see:
- **[EXAMPLES.md](EXAMPLES.md)** - Real-world use cases
- **[ADVANCED_FEATURES.md](ADVANCED_FEATURES.md)** - Advanced features
- **[KOKORO_SETUP.md](KOKORO_SETUP.md)** - Model setup guide