# Reader: Professional Audiobook Production CLI

[![PyPI](https://img.shields.io/pypi/v/reader)](https://pypi.org/project/reader/)
[![Python](https://img.shields.io/pypi/pyversions/reader)](https://pypi.org/project/reader/)
[![License](https://img.shields.io/pypi/l/reader)](https://github.com/dcrsn/reader/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/reader)](https://pypi.org/project/reader/)

**Transform long-form text into professional audiobooks with character-aware voices, emotion analysis, and intelligent processing.**

Perfect for novels, articles, textbooks, research papers, and any long-form content. Built with Kokoro-82M TTS for production-quality narration. Works on all platforms with optimizations for Apple Silicon (M1/M2/M3/M4 Neural Engine), NVIDIA GPUs, and AMD/Intel GPUs.

## ✨ Core Features

### ⚡ **High-Performance Conversion**
- **Up to 6x faster than real-time** on Apple Silicon (M1/M2/M3/M4) with Neural Engine
- **GPU acceleration** for NVIDIA (CUDA), AMD/Intel (DirectML on Windows)
- **Efficient CPU processing** on all platforms
- Kokoro-82M engine optimized for speed + quality balance

### 🎭 **Character-Aware Narration**
- **Automatic character detection** in dialogue
- **Auto-assign different voices** with automatic gender detection when possible
- Assigns gender-appropriate voices (e.g., Alice gets `af_sarah`, Bob gets `am_adam`)
- Perfect for fiction, interviews, dialogues, and multi-speaker content

### 😊 **Emotion Analysis**
- **VADER sentiment analysis** adjusts prosody in real-time
- Excitement, sadness, tension automatically reflected in voice tone
- Natural emotional narration without manual SSML tagging

### 💾 **Checkpoint Resumption**
- **Resume interrupted conversions** from where you left off
- Essential for extra-long texts (500+ page books, textbooks, research papers)
- Reliable production workflow for lengthy content

### 📚 **Chapter Management**
- **Automatic chapter detection** from EPUB TOC, PDF structure, or text patterns
- **M4B audiobook format** with chapter metadata
- Chapter timestamps and navigation

### 📊 **Professional Production Tools**
- **4 progress visualization styles**: simple, tqdm, rich, timeseries charts
- **Real-time metrics**: processing speed, ETA, completion percentage
- **Batch processing** with queue management
- **Multiple output formats**: MP3 (48kHz mono optimized), WAV, M4A, M4B

### 🎙️ **Production-Quality TTS**
- **Kokoro-82M**: 48 high-quality neural voices across 8 languages
- **Near-human quality** narration
- **Consistent voice** throughout long documents
- No voice cloning overhead

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

## 📦 Installation

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

### Using Poetry (for development)
```bash
# Clone the repository
git clone https://github.com/dcrsn/reader.git
cd reader

# Default installation
poetry install

# With optional extras
poetry install --extras "progress-full"

# Install all extras
poetry install --extras "all"
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
# Using pip
pip install audiobook-reader
pip uninstall onnxruntime
pip install onnxruntime-gpu

# Using poetry
poetry remove onnxruntime
poetry add onnxruntime-gpu
```

#### ✅ AMD/Intel GPU (Windows)
Get **DirectML acceleration**:

```bash
# Using pip
pip install audiobook-reader
pip uninstall onnxruntime
pip install onnxruntime-directml

# Using poetry
poetry remove onnxruntime
poetry add onnxruntime-directml
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

# 2. Models auto-download on first use (~310MB)
#    Or manually: reader download-models

# 3. Add a text file
echo "Hello world! This is my first audiobook." > text/hello.txt

# 4. Convert to audiobook (Neural Engine optimized)
reader convert

# 5. Listen to finished/hello_kokoro_am_michael.mp3
```

### 🎭 Character Voices (Optional)

For books with dialogue, assign different voices to each character:

```bash
# Auto-detect characters and generate config
poetry run reader characters detect text/mybook.txt --auto-assign

# OR manually create mybook.characters.yaml:
# characters:
#   - name: Alice
#     voice: af_sarah
#     gender: female
#   - name: Bob
#     voice: am_michael
#     gender: male

# Convert with character voices
poetry run reader convert --characters --file text/mybook.txt
```

## 📖 Documentation

- **[Usage Guide](docs/USAGE.md)** - Complete command reference and workflows
- **[Examples](docs/EXAMPLES.md)** - Real-world examples and use cases
- **[Phase 3 Features](docs/PHASE3_FEATURES.md)** - Advanced audiobook production features
- **[Kokoro Setup](docs/KOKORO_SETUP.md)** - Neural TTS model setup guide

## 🎙️ Command Reference

### Basic Conversion
```bash
# Convert single file with Neural Engine acceleration
poetry run reader convert --file text/book.epub

# Convert with specific voice
poetry run reader convert --file text/book.epub --voice am_michael

# Kokoro is the only engine in this package
# For limited storage/processing power, see reader-small package

# Enable debug mode to see Neural Engine status
poetry run reader convert --file text/book.epub --debug
```

### 📊 Progress Visualization Options

```bash
# Simple text progress (default)
poetry run reader convert --progress-style simple --file "book.epub"

# Professional progress bars with speed metrics  
poetry run reader convert --progress-style tqdm --file "book.epub"

# Beautiful Rich formatted displays with colors
poetry run reader convert --progress-style rich --file "book.epub"

# Real-time ASCII charts showing processing speed
poetry run reader convert --progress-style timeseries --file "book.epub"
```

### Configuration Management
```bash
# Save permanent settings to config file
poetry run reader config --engine kokoro --voice am_michael --format mp3

# List available voices (both pyttsx3 and Kokoro)
poetry run reader voices

# View current configuration
poetry run reader config

# View application info and features
poetry run reader info
```

### **Parameter Hierarchy (How Settings Work)**
1. **CLI parameters** (highest priority) - temporary overrides, never saved
2. **Config file** (middle priority) - your saved preferences  
3. **Code defaults** (lowest priority) - sensible fallbacks

Example:
```bash
# Save your preferred settings
poetry run reader config --engine kokoro --voice am_michael --format mp3

# Use temporary override (doesn't change your saved config)  
poetry run reader convert --engine pyttsx3 --voice af_sarah

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

### Output Formats
- **MP3** (default) - 48kHz mono, optimized for audiobooks
- **WAV** - Uncompressed, high quality
- **M4A** - Apple-friendly format
- **M4B** - Audiobook format with chapter support

## 🏗️ Project Structure

```
reader/
├── text/                   # 📂 Input files (your books)
├── audio/                  # 🔊 Temporary processing
├── finished/               # ✅ Completed audiobooks
├── config/                 # ⚙️ Configuration files
├── models/                 # 🤖 Kokoro TTS models
└── reader/
    ├── engines/           # 🎙️ TTS engines (Kokoro, pyttsx3)
    ├── parsers/           # 📖 File format parsers
    ├── batch/             # 💾 Neural Engine processor
    ├── analysis/          # 🎭 Emotion/dialogue detection
    └── cli.py             # 💻 Command-line interface
```

## 🎨 Example Workflows

### Simple Book Conversion
```bash
# Add your book
cp "My Novel.epub" text/

# Convert with Neural Engine acceleration
poetry run reader convert

# Result: finished/My Novel_kokoro_am_michael.mp3
```

### Voice Comparison
```bash
# Test different Kokoro voices on same content
poetry run reader convert --voice af_sarah --file text/sample.txt
poetry run reader convert --voice am_adam --file text/sample.txt
poetry run reader convert --voice bf_emma --file text/sample.txt

# Compare finished/sample_*.mp3 outputs
```

### Batch Processing
```bash
# Add multiple books
cp book1.epub book2.pdf story.txt text/

# Set default voice and convert all
poetry run reader config --voice am_michael --speed 1.0
poetry run reader convert

# Results: finished/book1_*.mp3, finished/book2_*.mp3, finished/story_*.mp3
```

## ⚙️ Configuration

Settings are saved to `config/settings.yaml`:

```yaml
tts:
  engine: kokoro           # TTS engine (kokoro or pyttsx3)
  voice: am_michael        # Default voice
  speed: 1.0               # Speech rate multiplier
  volume: 1.0              # Volume level
audio:
  format: mp3              # Output format (mp3, wav, m4a, m4b)
  add_metadata: true       # Metadata support
processing:
  chunk_size: 400          # Text chunk size for processing (Kokoro optimal)
  auto_detect_chapters: true  # Chapter detection
```

## 🛠️ Development

**Modular Architecture Benefits:**
- **Easy TTS upgrades**: pyttsx3 → Kokoro → Custom engines
- **New format support**: Add parsers for Word, HTML, etc.  
- **Enhanced processing**: Audio effects, normalization, etc.
- **Cloud integration**: Azure, AWS, Google TTS services

**Component Swapping:**
```python
# Each component implements abstract interfaces
class MyCustomTTS(TTSEngine):
    def synthesize(self, text, voice, speed): ...
    def list_voices(self): ...
```

## 🎯 Quick Examples

See **[docs/EXAMPLES.md](docs/EXAMPLES.md)** for detailed examples including:
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
- **Audio Quality**: 48kHz mono MP3, professional audiobook standard
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
- ✅ 48 voices across 8 languages
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
# Manual download via CLI
reader download-models

# Check cache location
# macOS: ~/Library/Caches/audiobook-reader/models/
# Linux: ~/.cache/audiobook-reader/models/
# Windows: %LOCALAPPDATA%\audiobook-reader\models\
```

### Neural Engine Not Detected (Apple Silicon)
**Error**: `Neural Engine not available, using CPU`

**Solution**:
- Ensure you're on Apple Silicon (M1/M2/M3/M4 Mac)
- Update macOS to latest version
- Reinstall onnxruntime: `poetry remove onnxruntime && poetry add onnxruntime`
- CPU fallback works fine but is slower

### Permission Errors
**Error**: `Permission denied` when creating directories

**Solution**:
```bash
# Ensure write permissions in project directory
chmod -R u+w /path/to/reader

# Or run from a directory you own
cd ~/Documents
git clone https://github.com/dcrsn/reader.git
cd reader
```

### Import Errors
**Error**: `ModuleNotFoundError: No module named 'kokoro_onnx'`

**Solution**:
```bash
# Reinstall dependencies
poetry install

# Or if using pip
pip install --force-reinstall reader
```

### Invalid Input Format
**Error**: `Unsupported file format`

**Supported formats**: `.epub`, `.pdf`, `.txt`, `.md`, `.rst`

**Solution**:
```bash
# Convert your file to a supported format first
# For Word docs: Save as .txt or .pdf
# For HTML: Save as .txt or use pandoc to convert
```

### GPU Acceleration Issues
**NVIDIA GPU**: Requires `onnxruntime-gpu` instead of `onnxruntime`
```bash
poetry remove onnxruntime
poetry add onnxruntime-gpu
```

**AMD/Intel GPU (Windows)**: Requires `onnxruntime-directml`
```bash
poetry remove onnxruntime
poetry add onnxruntime-directml
```

### Still Having Issues?
- Check the [GitHub Issues](https://github.com/dcrsn/reader/issues)
- Run with debug mode: `reader convert --debug --file yourfile.txt`
- Verify Python version: `python --version` (requires 3.10-3.13)

## 📜 Credits & Licensing

### Kokoro TTS Model
This project uses the [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) text-to-speech model by [hexgrad](https://github.com/hexgrad/kokoro), licensed under Apache 2.0.

**Model Credits:**
- Original Model: [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache 2.0)
- ONNX Wrapper: [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) by thewh1teagle (MIT)
- Training datasets: Koniwa (CC BY 3.0), SIWIS (CC BY 4.0)

### Reader Package
This audiobook CLI tool is licensed under the MIT License. See `LICENSE` file for details.

---

**Ready to create your first audiobook?** Check out the **[Usage Guide](docs/USAGE.md)** for step-by-step instructions!