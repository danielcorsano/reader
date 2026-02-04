# Audiobook Reader: a CLI Tool with GPU & NPU Acceleration

[![PyPI](https://img.shields.io/pypi/v/audiobook-reader)](https://pypi.org/project/audiobook-reader/)
[![Python](https://img.shields.io/pypi/pyversions/audiobook-reader)](https://pypi.org/project/audiobook-reader/)
[![Downloads](https://img.shields.io/pypi/dm/audiobook-reader)](https://pypi.org/project/audiobook-reader/)

**Transform long-form text into audiobooks with realistic, dialogue-aware AI voices.**

Perfect for novels, articles, textbooks, research papers, and other long-form content that you want to be able to listen to on your own time or offline. Built with Kokoro-82M TTS for production-quality narration. Works on all platforms with optimizations for Apple Silicon (M1/M2/M3/M4 Neural Engine), NVIDIA GPUs, and AMD/Intel GPUs.

If you find this useful, please consider supporting via [GitHub Sponsors](https://github.com/sponsors/danielcorsano).

## ✨ Core Features

### ⚡ **High-Performance Conversion**
- **Up to 8x faster than real-time** on Apple Silicon (M1/M2/M3/M4) with Neural Engine
- **GPU acceleration** for NVIDIA (CUDA), AMD/Intel (DirectML on Windows)
- **Efficient CPU processing** on all platforms
- Kokoro-82M engine optimized for speed + quality balance

### 🎭 **Character-Aware Narration**
- **Automatic character detection** in dialogue
- **Auto-assign different voices** with automatic gender detection where possible
- Assigns gender-appropriate voices (e.g., Alice gets `af_sarah`, Bob gets `am_adam`)
- Perfect for fiction, interviews, dialogues, and multi-speaker content

### 💾 **Checkpoint Resumption**
- **Resume interrupted conversions** from where you left off
- Essential for extra-long texts (500+ page books, textbooks, research papers)
- Reliable production workflow for lengthy content

### 📚 **Chapter Management**
- **Automatic chapter detection** from EPUB TOC, PDF structure, or text patterns
- **M4B audiobook format** with chapter metadata
- Chapter timestamps and navigation

### 📊 **Professional Production Tools**
- **4 progress visualization styles**: simple, tqdm, rich, timeseries
- **Real-time metrics**: processing speed, ETA, completion percentage
- **Batch processing** with queue management
- **Multiple output formats**: MP3 (48kHz mono optimized by default), WAV, M4A, M4B

### 🎙️ **Production-Quality TTS**
- **Kokoro-82M**: 54 high-quality neural voices across 9 languages
- **Near-human quality** narration
- **Consistent voice** throughout long documents
- No voice cloning overhead

### ✂️ **Text Stripping (New Feature!)**
- **Text stripping (new feature!):** use the reader strip command to detect and parse sections and get rid of unnecessary text (table of contents, foreword, secondary literature, bibliography etc.)

---

## ⚖️ Copyright Notice

**IMPORTANT**: This software is a tool for converting text to audio. Users are solely responsible for:

- Ensuring they have the legal right to convert any text to audio
- Obtaining necessary permissions for copyrighted materials
- Complying with all applicable copyright laws and licensing terms
- Understanding that creating audiobooks from copyrighted text without authorization may constitute copyright infringement

**Recommended Use Cases:**
- ✅ Your own original content
- ✅ Public domain works
- ✅ Content you have explicit permission to convert
- ✅ Educational materials you legally own
- ✅ Open-source or Creative Commons licensed texts (per their terms)

The developers of audiobook-reader do not condone or support copyright infringement. By using this software, you agree to use it only for content you have the legal right to convert.

---

## 📚 Supported Input Formats

EPUB, PDF, TXT, Markdown, ReStructuredText

**Need to convert other formats first?** Use [convertext](https://pypi.org/project/convertext/) to convert DOCX, ODT, MOBI, HTML, and other document formats to supported formats like EPUB or TXT.

## 📦 Installation

### Prerequisites

**FFmpeg Required** - Install before using audiobook-reader:

```bash
# macOS
brew install ffmpeg

# Windows
winget install ffmpeg

# Linux
sudo apt install ffmpeg
```

FFmpeg is required for audio format conversion (MP3, M4A, M4B). Models (~310MB) auto-download on first use.

### Using pip (recommended for users)
```bash
# Default installation (Kokoro TTS + core features)
pip install audiobook-reader

# With all progress visualizations (tqdm, rich, plotext)
pip install audiobook-reader[progress-full]

# With system monitoring
pip install audiobook-reader[monitoring]

# With everything
pip install audiobook-reader[all]
```

### Hardware Acceleration Options

audiobook-reader works great on **all platforms**. For maximum performance, enable hardware acceleration:

#### ✅ Apple Silicon (M1/M2/M3/M4)
**Neural Engine (CoreML) works automatically** - no additional setup needed!

```bash
pip install audiobook-reader
# That's it! CoreML acceleration is built-in
```

#### ✅ NVIDIA GPU (Windows/Linux)
Get **CUDA acceleration** with a simple package swap:

```bash
pip install audiobook-reader
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

#### ✅ AMD/Intel GPU (Windows)
Get **DirectML acceleration**:

```bash
pip install audiobook-reader
pip uninstall onnxruntime
pip install onnxruntime-directml
```

#### ✅ CPU Only (All Platforms)
**No GPU? No problem!** The default installation works efficiently on any CPU:

```bash
pip install audiobook-reader
# Works great on Intel, AMD, ARM processors
```

## 🚀 Quick Start

```bash
# 1. Install
pip install audiobook-reader

# 2. Models auto-download on first use (~310MB to ~/.cache/)
#    Or manually: reader download models

# 3. Convert any text file directly
reader convert --file mybook.epub

# 4. Find your audiobook in ~/Downloads/mybook_kokoro_am_michael.mp3

# Choose output location:
reader convert --file mybook.epub --output-dir downloads  # ~/Downloads/ (default)
reader convert --file mybook.epub --output-dir same       # Next to source
reader convert --file mybook.epub --output-dir /custom    # Custom path
```

### 🎭 Character Voices (Optional)

For books with dialogue, assign different voices to each character:

```bash
# Auto-detect characters and generate config
reader characters detect text/mybook.txt --auto-assign

# OR manually create mybook.characters.yaml:
# characters:
#   - name: Alice
#     voice: af_sarah
#     gender: female
#   - name: Bob
#     voice: am_michael
#     gender: male

# Convert with character voices
reader convert --characters --file text/mybook.txt
```

### 🐍 Python API (Jupyter Notebooks & Scripts)

For programmatic access in Python scripts or Jupyter notebooks:

```python
import reader

# Simple conversion
output = reader.convert("mybook.epub")
print(f"Audiobook created: {output}")

# Advanced usage
from reader import Reader
r = Reader()
output = r.convert(
    "mybook.epub",
    voice="af_sarah",
    speed=1.2,
    character_voices=True,
    progress_style="tqdm"
)
```

See **[Programmatic API](https://github.com/danielcorsano/reader/blob/main/docs/API.md)** for full documentation.

## 📖 Documentation

- **[Usage Guide](https://github.com/danielcorsano/reader/blob/main/docs/USAGE.md)** - Complete command reference and workflows
- **[Programmatic API](https://github.com/danielcorsano/reader/blob/main/docs/API.md)** - Python API for Jupyter notebooks and scripts
- **[Examples](https://github.com/danielcorsano/reader/blob/main/docs/EXAMPLES.md)** - Real-world examples and use cases
- **[Advanced Features](https://github.com/danielcorsano/reader/blob/main/docs/ADVANCED_FEATURES.md)** - Professional audiobook production features
- **[Kokoro Setup](https://github.com/danielcorsano/reader/blob/main/docs/KOKORO_SETUP.md)** - Neural TTS model setup guide

## 🎙️ Command Reference

### Basic Conversion
```bash
# Convert single file with Neural Engine acceleration
reader convert --file text/book.epub

# Convert with specific voice
reader convert --file text/book.epub --voice am_michael

# Disable text cleanup (keep broken words, bibliography, etc.)
reader convert --file text/book.epub --no-clean-text

# Enable debug mode to see Neural Engine status
reader convert --file text/book.epub --debug
```

**Text Cleanup (Enabled by Default):**
- **Fixes broken words**: `"exam-\nple"` → `"example"` (common in PDFs)
- **Removes metadata**: ISBN lines, book catalogs
- **Skips non-narrative chapters**: TOC, Bibliography, Index, "About the Author", "Acknowledgments", etc.
- **Extracts narrative boundaries**: Excludes all front/back matter
- **Result**: Cleaner audio, faster processing, no mispronunciations or metadata narration
- **Opt-out**: Use `--no-clean-text` to disable

### 📊 Progress Visualization Options

```bash
# Simple text progress (default)
reader convert --progress-style simple --file "book.epub"

# Professional progress bars with speed metrics
reader convert --progress-style tqdm --file "book.epub"

# Beautiful Rich formatted displays with colors
reader convert --progress-style rich --file "book.epub"

# Real-time ASCII charts showing processing speed
reader convert --progress-style timeseries --file "book.epub"
```

### Text Stripping
```bash
# Interactively strip unwanted chapters from a book
reader strip book.epub

# Flow: detect chapters → display list → choose strip/keep → save → optionally convert
# Syntax examples:
#   s 0, 6-8   → Strip chapters 0, 6, 7, 8 (keep the rest)
#   k 1-5      → Keep chapters 1-5 only (strip the rest)
# Output: book_stripped.epub (saved next to original)
```

### Configuration Management
```bash
# Save permanent settings to config file
reader config --voice am_michael --format mp3 --output-dir downloads

# Set custom default output directory
reader config --output-dir /audiobooks
reader config --output-dir same  # Save next to source files

# List available Kokoro voices
reader voices

# View current configuration
reader config

# View application info and features
reader info
```

### **Parameter Hierarchy (How Settings Work)**
1. **CLI parameters** (highest priority) - temporary overrides, never saved
2. **Config file** (middle priority) - your saved preferences  
3. **Code defaults** (lowest priority) - sensible fallbacks

Example:
```bash
# Save your preferred settings
reader config --engine kokoro --voice am_michael --format mp3

# Use temporary override (doesn't change your saved config)
reader convert --voice af_sarah

# Your config file still has kokoro/am_michael/mp3 saved
```

## 📁 File Support

### Input Formats
| Format | Extension | Chapter Detection |
|--------|-----------|------------------|
| EPUB | `.epub` | ✅ Automatic from TOC |
| PDF | `.pdf` | ✅ Page-based |
| Text | `.txt` | ✅ Simple patterns |
| Markdown | `.md` | ✅ Header-based |
| ReStructuredText | `.rst` | ✅ Header-based |

**Need other formats?** Use [convertext](https://pypi.org/project/convertext/) to convert DOCX, ODT, MOBI, HTML, and more to supported formats.

### Output Formats
- **MP3** (default) - 48kHz mono, configurable bitrate (32k-64k, default 48k)
- **WAV** - Uncompressed, high quality
- **M4A** - Apple-friendly format
- **M4B** - Audiobook format with chapter support

## 🏗️ File Locations

Reader uses system-standard directories for clean organization:

**Working Files (Temporary):**
- **Temp workspace**: `/tmp/audiobook-reader-{session}/` (auto-cleaned on exit)
- Session-specific, isolated from your files
- Automatically removed when conversion completes

**Persistent Data:**
- **Models**: `~/.cache/audiobook-reader/models/` (~310MB, shared across all conversions)
- **Config**: `~/.config/audiobook-reader/` (settings and character mappings)

**Output Files (Your Audiobooks):**
- **Default**: `~/Downloads/` (configurable)
- **Options**:
  - `--output-dir downloads` → `~/Downloads/`
  - `--output-dir same` → Next to source file
  - `--output-dir /custom/path` → Custom location

**No directory pollution** - only your final audiobooks appear in the output location!

## 🎨 Example Workflows

### Simple Book Conversion
```bash
# Convert any book directly
reader convert --file "My Novel.epub"

# Result: ~/Downloads/My Novel_kokoro_am_michael.mp3

# Or output next to source file
reader convert --file "My Novel.epub" --output-dir same

# Result: My Novel_kokoro_am_michael.mp3 (in same directory as source)
```

### Voice Comparison
```bash
# Test different Kokoro voices on same content
reader convert --voice af_sarah --file text/sample.txt
reader convert --voice am_adam --file text/sample.txt
reader convert --voice bf_emma --file text/sample.txt

# Compare finished/sample_*.mp3 outputs
```

### Strip and Convert
```bash
# Strip unnecessary chapters before converting
reader strip "Philosophy Textbook.epub"
# → Shows chapters, you pick which to keep
# → Saves Philosophy Textbook_stripped.epub
# → Asks "Convert to audiobook?" — say yes to convert immediately

# Or strip first, convert separately
reader strip book.pdf
reader convert --file book_stripped.txt
```

### Batch Processing
```bash
# Convert multiple files with custom output location
reader convert --file book1.epub --output-dir /audiobooks
reader convert --file book2.pdf --output-dir /audiobooks
reader convert --file story.txt --output-dir /audiobooks

# Results: /audiobooks/book1_*.mp3, /audiobooks/book2_*.mp3, /audiobooks/story_*.mp3

# Or set default output directory in config
reader config --output-dir /audiobooks
reader convert --file book1.epub  # → /audiobooks/
```

## ⚙️ Configuration

Settings are saved to `~/.config/audiobook-reader/settings.yaml`:

```yaml
tts:
  engine: kokoro           # TTS engine (Kokoro)
  voice: am_michael        # Default voice
  speed: 1.0               # Speech rate multiplier
  volume: 1.0              # Volume level
audio:
  format: mp3              # Output format (mp3, wav, m4a, m4b)
  bitrate: 48k             # MP3 bitrate (32k-64k typical for audiobooks)
  add_metadata: true       # Metadata support
processing:
  chunk_size: 400          # Text chunk size for processing (Kokoro optimal)
  auto_detect_chapters: true  # Chapter detection
output_dir: downloads      # Output location: "downloads", "same", or path
```

## 🎯 Quick Examples

See **[docs/EXAMPLES.md](https://github.com/danielcorsano/reader/blob/main/docs/EXAMPLES.md)** for detailed examples including:
- Voice testing and selection
- PDF processing workflows  
- Markdown chapter handling
- Batch processing scripts
- Configuration optimization

## 📊 Technical Specs

- **TTS Engine**: Kokoro-82M (82M parameters, Apache 2.0 license)
- **Model Size**: ~310MB ONNX models (auto-downloaded on first use to cache)
- **Model Cache**: Follows XDG standard (`~/.cache/audiobook-reader/models/`)
- **Python**: 3.10-3.13 compatibility
- **Platforms**: macOS, Linux, Windows (all fully supported)
- **Audio Quality**: 48kHz mono MP3, configurable bitrate (32k-64k, default 48k)
- **Hardware Acceleration**:
  - ✅ Apple Silicon (M1/M2/M3/M4): CoreML (Neural Engine) - automatic
  - ✅ NVIDIA GPUs: CUDA via onnxruntime-gpu
  - ✅ AMD/Intel GPUs: DirectML on Windows
  - ✅ CPU: Works efficiently on all processors
- **Performance**: Hardware-accelerated on all major platforms
- **Memory**: Efficient streaming processing for large books

## 🎵 Audio Quality

**Kokoro TTS** (primary engine):
- ✅ Near-human quality neural voices
- ✅ 54 voices across 9 languages (American/British English, Spanish, French, Italian, Portuguese, Japanese, Chinese, Hindi)
- ✅ Apple Neural Engine acceleration
- ✅ Professional audiobook production
- ✅ Consistent narration (no hallucinations)

---

## 🔧 Troubleshooting

### FFmpeg Not Found
**Error**: `FFmpeg not found` or `Command 'ffmpeg' not found`

**Solution**:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
# Or use: choco install ffmpeg
```

### Models Not Downloading
**Error**: `Failed to download Kokoro models`

**Solution**:
Models auto-download on first use (~310MB). If automatic download fails:
```bash
# Download to system cache (default)
reader download models

# Download to local models/ folder (permanent storage)
reader download models --local

# Force re-download
reader download models --force
```

**Model & File Locations:**
- **Models**: `~/.cache/audiobook-reader/models/` (all platforms, ~310MB)
- **Config**: `~/.config/audiobook-reader/` (settings and character mappings)
- **Temp Files**: `/tmp/audiobook-reader-{session}/` (auto-cleaned on exit)
- **Output**: `~/Downloads/` by default (configurable with `--output-dir`)

### Neural Engine Not Detected (Apple Silicon)
**Error**: `Neural Engine not available, using CPU`

**Solution**:
- Ensure you're on Apple Silicon (M1/M2/M3/M4 Mac)
- Update macOS to latest version
- Reinstall onnxruntime: `pip uninstall onnxruntime && pip install onnxruntime`
- CPU processing works fine but is slower than GPU/NPU

### Permission Errors
**Error**: `Permission denied` when creating directories

**Solution**:
```bash
# Ensure write permissions in project directory
chmod -R u+w /path/to/reader

# Or run from a directory you own
cd ~/Documents
git clone https://github.com/danielcorsano/reader.git
cd reader
```

### Import Errors
**Error**: `ModuleNotFoundError: No module named 'kokoro_onnx'`

**Solution**:
```bash
# Reinstall package
pip install --force-reinstall audiobook-reader
```

### Invalid Input Format
**Error**: `Unsupported file format`

**Supported formats**: `.epub`, `.pdf`, `.txt`, `.md`, `.rst`

**Solution**:
```bash
# Use convertext to convert other formats first
pip install convertext
convertext document.docx --format epub  # DOCX to EPUB
convertext book.mobi --format epub      # MOBI to EPUB
convertext file.html --format txt       # HTML to TXT

# Then convert to audiobook
reader convert --file document.epub
```

### GPU Acceleration Issues
**NVIDIA GPU**: Requires `onnxruntime-gpu` instead of `onnxruntime`
```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

**AMD/Intel GPU (Windows)**: Requires `onnxruntime-directml`
```bash
pip uninstall onnxruntime
pip install onnxruntime-directml
```

### Still Having Issues?
- Check the [GitHub Issues](https://github.com/danielcorsano/reader/issues)
- Run with debug mode: `reader convert --debug --file yourfile.txt`
- Verify Python version: `python --version` (requires 3.10-3.13)

## 📜 Credits

### Kokoro TTS Model
This project uses the [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) text-to-speech model by [hexgrad](https://github.com/hexgrad/kokoro), licensed under Apache 2.0.

**Model Credits:**
- Original Model: [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache 2.0)
- ONNX Wrapper: [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) by thewh1teagle (MIT)
- Training datasets: Koniwa (CC BY 3.0), SIWIS (CC BY 4.0)

## 💝 Support This Project

If you find this tool helpful, please consider [sponsoring the project](https://github.com/sponsors/danielcorsano). I created and maintain this software alone as a public service, and donations help me improve it and develop requested features. If I get $99 of donations, I will use it to pay for the Apple developer program so I can make iOS versions of all my open source apps.

Your support makes a real difference in keeping this project active and growing. Thank you!

### License
This tool is licensed under the MIT License. See `LICENSE` file for details.

**Ready to create your first audiobook?** Check out the **[Usage Guide](https://github.com/danielcorsano/reader/blob/main/docs/USAGE.md)** for step-by-step instructions!
