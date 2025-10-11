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

# Emotional preview with custom text
reader preview af_sarah --emotion dramatic --text "This is a test of dramatic narration!"

# Save previews to specific directory
reader preview af_michael --output-dir voice_tests/
```

### Emotional Styles Available

- `neutral` - Standard reading voice
- `excited` - Energetic and enthusiastic  
- `sad` - Melancholy and slow
- `angry` - Intense and forceful
- `whisper` - Soft and intimate
- `dramatic` - Theatrical with emphasis

### Voice Comparison Workflow

```bash
# Create multiple previews for comparison
reader preview af_sarah --emotion neutral --output-dir comparison/
reader preview af_nicole --emotion neutral --output-dir comparison/
reader preview bf_emma --emotion neutral --output-dir comparison/

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

## 🎭 Dialogue Detection & Context Analysis

### Advanced Text Processing

The system analyzes text for intelligent voice assignment:

```bash
# Enable dialogue detection
reader convert novel.txt --dialogue

# Combine with character voices
reader convert novel.txt --dialogue --characters --emotion
```

### How It Works

1. **Dialogue Identification**: Finds quoted speech vs narration
2. **Speaker Detection**: Attempts to identify who is speaking
3. **Context Analysis**: Classifies narrative type (action, description, thought)
4. **Emotion Context**: Detects emotional tone from punctuation and keywords

### Example Analysis Output

For text: `"I can't believe it!" Sarah exclaimed excitedly.`

- **Is Dialogue**: Yes
- **Speaker**: Sarah  
- **Emotion**: Excitement
- **Context**: Speech with attribution

This enables:
- **Different voices** for different characters
- **Emotional prosody** based on context
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
# Enable character-specific voices with emotion analysis
reader config --characters --emotion --dialogue
```

---

## 📚 Complete Workflow Examples

### Example 1: Single Book Production

```bash
# Setup for high-quality audiobook
reader config --format m4b

# Preview voices to choose narrator
reader preview af_sarah --emotion neutral
reader preview bf_emma --emotion neutral

# Extract and review chapters
reader chapters extract novel.epub --output analysis.json

# Convert with all features
reader convert novel.epub --voice af_sarah --chapters --dialogue --emotion

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

# Convert with character mapping
reader convert harry_potter.epub --characters --dialogue --emotion

# Characters will automatically use assigned voices
```

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
- **Solution**: Install with `poetry install` (The system dependencies)

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