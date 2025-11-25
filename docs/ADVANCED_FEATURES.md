# Advanced Features Documentation

## Overview

Professional audiobook production system with advanced features for processing, analysis, and batch conversion.

---

## 📖 Chapter Management

### Automatic Chapter Detection

The system intelligently detects chapters using multiple methods:

1. **Pattern Recognition**: "Chapter 1", "Chapter One", "Part I", etc.
2. **Structure Analysis**: Paragraph breaks and formatting
3. **File Metadata**: EPUB/PDF built-in chapter markers

### Examples

```bash
# Extract chapter structure from any book
reader chapters extract book.epub

# Save chapter metadata to JSON
reader chapters extract book.pdf --output chapters.json --format json

# Generate text report
reader chapters extract novel.txt --output report.txt --format text
```

### Chapter Output Example

```json
{
  "chapters": [
    {
      "title": "Chapter 1: The Meeting",
      "start_time": 0.0,
      "end_time": 38.0,
      "duration": 38.0,
      "word_count": 95,
      "chapter_number": 1
    }
  ],
  "total_chapters": 2,
  "total_duration": 69.2,
  "total_words": 173
}
```

### Use Cases

- **M4B Creation**: Chapter markers for professional audiobooks
- **Progress Tracking**: Know exactly how long each chapter will take
- **Quality Control**: Identify chapters that are too long/short
- **Voice Planning**: Assign different voices per chapter/character

---

## 🎙️ Voice Preview System

### Test Voices Before Converting

Generate audio samples to choose the perfect narrator:

```bash
# Basic voice preview
reader preview af_sarah --engine kokoro

# Preview with custom text
reader preview af_sarah --text "This is a test of dramatic narration!"

# Save previews to specific directory
reader preview af_michael --output-dir voice_tests/
```

### Voice Comparison Workflow

```bash
# Create multiple previews for comparison
reader preview af_sarah --output-dir comparison/
reader preview af_nicole --output-dir comparison/
reader preview bf_emma --output-dir comparison/

# Listen to all previews and choose your favorite
ls comparison/
# preview_kokoro_af_sarah_neutral.wav
# preview_kokoro_af_nicole_neutral.wav  
# preview_kokoro_bf_emma_neutral.wav
```

---

## 🔄 Batch Processing & Checkpoint System

### Efficient Stream-to-File Processing

Process books with minimal memory usage and automatic resume capability:

```bash
# Convert with automatic checkpoints
reader convert book.epub --voice am_michael --engine kokoro

# Resume interrupted conversion (detects existing progress automatically)
reader convert book.epub

# Custom checkpoint frequency (default: every 50 chunks)
reader convert book.epub --checkpoint-interval 100
```

### How Stream Checkpoints Work

- **Zero Memory Overhead**: Audio streams directly to output file
- **Tiny Checkpoints**: Only metadata saved (< 1KB), not audio segments  
- **Smart Resume**: Detects setting changes and starts fresh when needed
- **File Integrity**: Verifies partial files before resuming
- **Thermal Management**: Built-in CPU monitoring and throttling

### Checkpoint Benefits

- ✅ **Interruption Safe**: Ctrl+C, crashes, or reboots won't lose progress
- ✅ **Memory Efficient**: No RAM overhead for long audiobooks
- ✅ **Disk Efficient**: No temporary files or segment storage
- ✅ **Settings Aware**: Automatically restarts if voice/quality changes

### Queue-Based Bulk Conversion

Process multiple books efficiently with parallel workers:

### Adding Jobs to Queue

```bash
# Add individual files
reader batch add book1.epub book2.pdf novel.txt

# Add entire directory
reader batch add --directory books/ --output-dir audiobooks/

# Add recursively with custom output
reader batch add --directory library/ --recursive --output-dir converted/
```

### Processing the Queue

```bash
# Process with default settings (2 workers)
reader batch process

# Use more workers for faster processing
reader batch process --max-workers 4

# Save progress to resume later
reader batch process --save-progress
```

### Queue Management

```bash
# Check current queue status
reader batch status

# Clear all pending jobs
reader batch clear
```

### Real-World Example: Converting a Library

```bash
# Setup: Convert entire book collection
reader config --format m4b  # Professional audiobook format

# Add all books recursively
reader batch add --directory ~/Books/ --recursive --output-dir ~/Audiobooks/

# Check what was added
reader batch status
# Output:
# Batch Queue Status:
#   Total jobs: 47
#   Running: False
#   Job status breakdown:
#     pending: 47

# Process with 4 parallel workers
reader batch process --max-workers 4 --save-progress

# Monitor progress (real-time updates)
# ✓ harry_potter_1.epub - completed
# ✓ lord_of_rings.pdf - completed  
# ⏳ dune.txt - running
# ✗ broken_file.epub - failed
```

### Error Handling & Recovery

- **Individual Failures**: Other books continue processing
- **Progress Saving**: Resume interrupted batches
- **Detailed Logging**: See exactly what failed and why
- **Automatic Retries**: Built-in retry logic for temporary failures

---

## 🔊 Advanced Audio Formats

### Professional Audiobook Production

The system supports multiple output formats with metadata:

```bash
# Standard MP3 with metadata
reader convert book.epub --format mp3

# M4A for Apple ecosystem
reader convert book.epub --format m4a

# M4B professional audiobook with chapters
reader convert book.epub --format m4b --chapters
```

### Format Comparison

| Format | Quality | Size | Features | Best For |
|--------|---------|------|----------|----------|
| WAV | Highest | Largest | Uncompressed | Editing/Master |
| MP3 | Good | Medium | Universal | General Use |
| M4A | High | Small | iTunes/Apple | Apple Devices |
| M4B | High | Small | Chapters + Bookmarks | Professional |

### Metadata & Chapter Support

M4B files include:
- **Chapter Markers**: Jump between chapters
- **Book Metadata**: Title, author, description
- **Artwork**: Cover images (when available)
- **Bookmarks**: Resume exactly where you left off

---

## 🧹 Text Cleanup & Preprocessing

### Automatic Content Filtering

Intelligent text processing ensures clean output:

```bash
# Text cleanup enabled by default
reader convert book.epub

# Disable for verbatim conversion
reader convert book.epub --no-clean-text
```

### What Gets Cleaned

**1. Broken Word Repair:**
- Fixes hyphenated words split across lines: `"exam-\nple"` → `"example"`
- Common in PDFs with poor text extraction
- Prevents TTS mispronunciation

**2. Metadata Removal:**
- ISBN lines automatically detected and removed
- Book catalog sections (e.g., "OTHER BOOKS BY THIS AUTHOR...")
- Only removes blocks >200 characters to avoid false positives

**3. Non-Narrative Chapter Filtering:**
Automatically skips chapters with these titles:
- Table of Contents
- Bibliography / References / Notes
- Index
- About the Author / About the Publisher
- Acknowledgments
- Books by [Author] / Other Works / Novels and Story Collections
- Praise for [Book]

**4. Narrative Boundary Extraction:**
- Identifies first narrative chapter (excludes all front matter)
- Identifies last narrative chapter (excludes all back matter)
- Rebuilds content only from narrative sections
- Prevents TOC text from bleeding into narration

### Benefits

- ✅ **Better pronunciation**: No broken words or ISBN sequences
- ✅ **Cleaner audio**: No bibliography or metadata narration
- ✅ **Faster processing**: 10-20% reduction on academic works
- ✅ **Conservative approach**: Minimal false positives

### Use Cases

**Enable (default):**
- Fiction novels (skip "About the Author")
- Non-fiction books (skip Bibliography, Index)
- Academic texts (skip References)
- PDFs with formatting issues

**Disable (`--no-clean-text`):**
- Technical documentation (keep all sections)
- Legal documents (verbatim required)
- Poetry collections (preserve formatting)
- Reference materials (need index/bibliography)

### Example: PDF Academic Book

```bash
# Before cleanup: 450 pages including 80 pages of references
reader convert textbook.pdf --no-clean-text
# Result: 18 hour audiobook including all references

# With cleanup (default):
reader convert textbook.pdf
# Result: 15 hour audiobook, narrative content only
# Saved: 3 hours of bibliography narration
```

---

## 🎭 Dialogue Detection & Context Analysis

### Advanced Text Processing

The system analyzes text for intelligent voice assignment:

```bash
# Enable character voices (automatically enables dialogue detection)
reader convert novel.txt --characters
```

### How It Works

1. **Dialogue Identification**: Finds quoted speech vs narration
2. **Speaker Detection**: Attempts to identify who is speaking
3. **Context Analysis**: Classifies narrative type (action, description, thought)

### Example Analysis Output

For text: `"I can't believe it!" Sarah exclaimed excitedly.`

- **Is Dialogue**: Yes
- **Speaker**: Sarah
- **Context**: Speech with attribution

This enables:
- **Different voices** for different characters
- **Narrative vs dialogue** distinction

---

## 🔧 Configuration Management

### Per-Project Settings

```bash
# View current configuration
reader config

# Sample output:
# Current configuration:
#   Engine: kokoro  
#   Voice: default
#   Speed: 1.0x
#   Audio format: wav
#   Advanced Features:
#     Dialogue detection: true
#     Advanced audio formats: true
#     Chapter metadata: true
```

### Workflow-Specific Configs

```bash
# Enable character-specific voices (dialogue detection auto-enabled)
reader config --characters
```

---

## 📚 Complete Workflow Examples

### Example 1: Single Book Production

```bash
# Setup for high-quality audiobook
reader config --format m4b

# Preview voices to choose narrator
reader preview af_sarah
reader preview bf_emma

# Extract and review chapters
reader chapters extract novel.epub --output analysis.json

# Convert with chapters
reader convert novel.epub --voice af_sarah --chapters

# Result: professional M4B audiobook with chapters and metadata
```

### Example 2: Bulk Library Conversion

```bash
# Setup batch processing
reader config --format mp3

# Add entire library
reader batch add --directory ~/ebooks/ --recursive --output-dir ~/audiobooks/

# Process in parallel
reader batch process --max-workers 6 --save-progress

# Monitor and manage
reader batch status
reader batch clear  # if needed
```

### Example 3: Character Voice Mapping

```bash
# Setup character voices for a novel
reader characters add "Harry" "af_michael"
reader characters add "Hermione" "af_sarah"  
reader characters add "Hagrid" "bf_oliver"

# Create voice blends for unique characters
reader blend create "wizard_voice" "af_michael:70,bf_oliver:30"

# Convert with character mapping (dialogue detection automatic)
reader convert harry_potter.epub --characters

# Characters will automatically use assigned voices
```

---

## ⚙️ Project-Level Configuration

### Overview

Reader's multi-layer configuration system enables sophisticated workflows with minimal setup. Config files are inherited through your directory tree, making it perfect for organizing large audiobook libraries or team projects.

### Use Case 1: Fiction vs Non-Fiction Libraries

**Scenario:** You have separate libraries for fiction and non-fiction, each requiring different narration styles.

**Setup:**

```bash
~/audiobooks/
├── fiction/
│   ├── .reader.yaml          # Fiction-specific settings
│   ├── scifi/
│   ├── mystery/
│   └── fantasy/
└── non-fiction/
    ├── .reader.yaml          # Non-fiction-specific settings
    ├── history/
    ├── science/
    └── business/
```

**Fiction config** (`~/audiobooks/fiction/.reader.yaml`):
```yaml
tts:
  voice: am_michael      # Dramatic, storytelling voice
  speed: 1.0             # Normal speed for immersion
processing:
  character_voices: true # Enable character detection
audio:
  format: m4b           # Audiobook format with chapters
```

**Non-Fiction config** (`~/audiobooks/non-fiction/.reader.yaml`):
```yaml
tts:
  voice: af_nicole       # Clear, professional voice
  speed: 1.3             # Faster for educational content
processing:
  character_voices: false
audio:
  format: mp3            # Standard format for lectures
```

**Result:** Any book in `fiction/` automatically gets character voices and storytelling narration. Books in `non-fiction/` get faster speed and clear professional voice - no CLI arguments needed!

### Use Case 2: Team Audiobook Production

**Scenario:** Multiple team members producing audiobooks need consistent settings.

**Setup:**

```bash
# Project lead creates config
cd audiobook-project/
cat > .reader.yaml << 'EOF'
tts:
  voice: bf_emma
  speed: 1.0
audio:
  format: m4b
  bitrate: 64k
processing:
  character_voices: true
output_dir: /shared/audiobooks/
EOF

# Check into version control
git add .reader.yaml
git commit -m "Add audiobook production config"
git push

# Team members clone and work
git clone project-url
cd audiobook-project/

# Everyone inherits same settings automatically
reader convert --file chapter1.txt
reader convert --file chapter2.txt
```

**Benefits:**
- Consistent quality across team
- No manual config copying
- Settings versioned with project
- Easy to update for everyone

### Use Case 3: Multi-Genre Production Studio

**Scenario:** Production studio handles multiple genres, each with specific requirements.

**Setup:**

```bash
~/production/
├── .reader.yaml                # Studio-wide defaults
├── clients/
│   ├── client-a/
│   │   ├── .reader.yaml       # Client A preferences
│   │   ├── book1/
│   │   └── book2/
│   └── client-b/
│       ├── .reader.yaml       # Client B preferences
│       ├── audiobook1/
│       └── audiobook2/
└── internal/
    ├── fiction/
    │   └── .reader.yaml
    └── non-fiction/
        └── .reader.yaml
```

**Studio defaults** (`~/production/.reader.yaml`):
```yaml
audio:
  format: m4b
  add_metadata: true
processing:
  auto_detect_chapters: true
output_dir: /production/output/
```

**Client A overrides** (`~/production/clients/client-a/.reader.yaml`):
```yaml
tts:
  voice: af_sarah
  speed: 1.1
audio:
  bitrate: 96k    # Premium quality for client A
```

**Result:** Files in `client-a/book1/` inherit:
- Studio defaults (format, output_dir, chapters)
- Client A overrides (voice, speed, bitrate)
- Config hierarchy ensures consistent quality with client-specific customization

### Use Case 4: Voice Testing Workflow

**Scenario:** Testing multiple voices for a book before committing to full production.

**Setup:**

```bash
# Extract sample chapter
mkdir voice-tests/
cp book.epub voice-tests/sample.epub

# Test voice 1
mkdir voice-tests/test-1/
cd voice-tests/test-1/
echo "tts:\n  voice: am_michael" > .reader.yaml
reader convert --file ../sample.epub

# Test voice 2
mkdir voice-tests/test-2/
cd voice-tests/test-2/
echo "tts:\n  voice: af_sarah" > .reader.yaml
reader convert --file ../sample.epub

# Test voice 3
mkdir voice-tests/test-3/
cd voice-tests/test-3/
echo "tts:\n  voice: bf_emma" > .reader.yaml
reader convert --file ../sample.epub

# Compare outputs in ~/Downloads/
ls ~/Downloads/sample_*
```

**Benefits:**
- Each test isolated by directory
- User config settings inherited (speed, format, etc.)
- Only voice changes between tests
- Easy to compare results

### Use Case 5: Monorepo Audiobook Collection

**Scenario:** Large collection with nested organization and inheritance.

**Setup:**

```bash
~/library/
├── .reader.yaml                # Global library defaults
├── english/
│   ├── .reader.yaml           # English-specific (inherits global)
│   ├── fiction/
│   │   ├── .reader.yaml       # Fiction settings (inherits english + global)
│   │   ├── scifi/
│   │   ├── fantasy/
│   │   └── mystery/
│   └── non-fiction/
│       └── .reader.yaml       # Non-fiction settings (inherits english + global)
└── spanish/
    ├── .reader.yaml           # Spanish-specific (inherits global)
    └── literature/
```

**Global** (`~/library/.reader.yaml`):
```yaml
audio:
  format: m4b
  add_metadata: true
processing:
  auto_detect_chapters: true
output_dir: /audiobooks/
```

**English** (`~/library/english/.reader.yaml`):
```yaml
tts:
  speed: 1.2
```

**English Fiction** (`~/library/english/fiction/.reader.yaml`):
```yaml
tts:
  voice: am_michael
processing:
  character_voices: true
```

**Result for** `~/library/english/fiction/scifi/dune.epub`:
- Global: m4b format, metadata, chapters, output dir
- English: speed 1.2
- Fiction: voice am_michael, character_voices true
- **All merged together automatically!**

### Configuration Search Behavior

Reader searches upward from your file's directory until it finds a config or reaches your home directory:

```bash
# Converting: ~/projects/audiobooks/fiction/book.epub

# Search order:
1. ~/projects/audiobooks/fiction/.reader.yaml         # Check here first
2. ~/projects/audiobooks/.reader.yaml                 # Then parent
3. ~/projects/.reader.yaml                            # Then parent
4. ~/.reader.yaml                                     # Then home
5. Stop search (don't go to system root)

# Uses first config found + user config (~/.config/audiobook-reader/config.yaml)
```

### Best Practices

1. **User config for personal defaults** - Set your preferred voice, speed, format once
2. **Project configs for overrides** - Only specify what changes from user defaults
3. **Use descriptive filenames** - `.reader.yaml` or `audiobook-reader.yaml` both work
4. **Version control project configs** - Great for team collaboration
5. **Test with samples first** - Create test directory with config to verify settings
6. **Organize by genre/client** - Use directory structure + configs for automatic organization

---

## 🚀 Performance & Optimization

### Speed vs Quality Tradeoffs

| Mode | Speed | Quality | Use Case |
|------|-------|---------|----------|
| Fast conversion | Fastest | Good | Quick drafts, testing |
| Standard conversion | Medium | High | Most audiobooks |
| Full feature conversion | Slower | Highest | Maximum quality with all features |

### Optimization Tips

1. **Use Basic mode** for initial testing and iteration
2. **Batch Processing** is more efficient than individual conversions
3. **Match workers** to your CPU cores (typically 2-8 workers)
4. **WAV format** is fastest, M4B takes longer due to processing
5. **Disable features** you don't need to improve speed

### Resource Usage

- **Memory**: ~50MB base (stream processing eliminates RAM overhead)
- **Storage**: WAV = ~10MB/min, MP3 = ~1MB/min, M4B = ~1MB/min
- **CPU**: Smart thermal management keeps usage under 75%
- **Checkpoints**: < 1KB metadata files (no temporary segments)

---

## 🆘 Troubleshooting

### Common Issues

**Kokoro Models Not Found**
```
Info: Kokoro models not yet downloaded. Will auto-download on first use.
```
- **Solution**: Models download automatically on first successful use with internet

**Format Conversion Fails**
```
Error: Format conversion requires FFmpeg and pydub
```
- **Solution**: FFmpeg must be installed separately (see troubleshooting section)

**Batch Queue Empty**
```
Batch Queue Status: Total jobs: 0
```
- **Solution**: Batch jobs don't persist between sessions (by design)

**Chapter Detection Poor**
- **Solution**: Try different file formats (EPUB > PDF > TXT for chapter detection)

### Getting Help

```bash
# View available commands
reader --help

# Get help for specific command
reader convert --help
reader batch --help
reader chapters --help
```

---

## 🎉 Summary

The system transforms a simple TTS tool into a professional audiobook production system:

- ✅ **Intelligent Processing**: multiple processing options for any workflow
- ✅ **Chapter Management**: Automatic detection and professional metadata  
- ✅ **Voice System**: Preview, compare, and assign voices intelligently
- ✅ **Batch Processing**: Efficient bulk conversion with progress tracking
- ✅ **Professional Output**: M4B format with chapters and metadata
- ✅ **Advanced Analysis**: Dialogue detection and context awareness

Perfect for individual authors, publishing houses, or anyone serious about audiobook production!