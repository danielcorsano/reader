# Reader: Professional Audiobook Production CLI

[![PyPI](https://img.shields.io/pypi/v/reader)](https://pypi.org/project/reader/)
[![Python](https://img.shields.io/pypi/pyversions/reader)](https://pypi.org/project/reader/)
[![License](https://img.shields.io/pypi/l/reader)](https://github.com/dcrsn/reader/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/reader)](https://pypi.org/project/reader/)

**Transform novels into professional audiobooks with character-aware voices, emotion analysis, and blazing-fast Neural Engine optimization.**

Built with Kokoro-82M TTS for production-quality narration. Optimized for Apple Silicon (M1/M2/M3) with significant performance advantages over CPU-only solutions.

## ✨ What Makes Reader Different

Unlike other audiobook tools, Reader is built for **professional novel narration** with features designed for long-form fiction:

### 🎭 **Character-Aware Narration** (Unique)
- **Auto-detect characters** in dialogue and assign different voices
- **Map voices to personalities**: Harry gets `am_adam`, Hermione gets `af_sarah`
- Perfect for novels with multiple POV characters

### 😊 **Emotion Analysis** (Unique)
- **VADER sentiment analysis** adjusts prosody in real-time
- Excitement, sadness, tension automatically reflected in voice tone
- Natural emotional narration without manual SSML tagging

### 💾 **Checkpoint Resumption** (Unique)
- Converting a 500-page novel? **Resume from where you left off** if interrupted
- No other tool offers this for long audiobook conversions
- Essential for reliable production workflows

### ⚡ **Blazing Performance on Apple Silicon**
- **Neural Engine (CoreML) optimization** for M1/M2/M3 Macs
- Processes audiobooks significantly faster than CPU-only solutions
- Kokoro-82M engine chosen for **speed + quality balance**

### 📊 **Professional Production Tools**
- **4 progress visualization styles** including real-time ASCII charts
- **Chapter detection and metadata** for M4B audiobook format
- **Batch processing** with queue management
- **Multiple output formats**: MP3 (48kHz mono optimized), WAV, M4A, M4B

### 🎙️ **Production-Quality TTS**
- **Kokoro-82M**: 48 high-quality neural voices across 8 languages
- **Near-human quality** without voice cloning overhead
- **Consistent narration** perfect for audiobooks

---

## 📚 Supported Input Formats

EPUB, PDF, TXT, Markdown, ReStructuredText

## 📦 Installation

### Using pip (recommended for users)
```bash
# Default installation (Kokoro TTS + core features)
pip install reader

# With all progress visualizations (tqdm, rich, plotext)
pip install reader[progress-full]

# With system monitoring
pip install reader[monitoring]

# With everything
pip install reader[all]
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

### GPU Acceleration

#### Apple Silicon (M1/M2/M3) ✅
The Neural Engine (CoreML) is used automatically - no additional setup needed!

#### NVIDIA GPU (Windows/Linux)
```bash
# Using pip
pip install reader
pip uninstall onnxruntime
pip install onnxruntime-gpu

# Using poetry
poetry remove onnxruntime
poetry add onnxruntime-gpu
```

#### AMD/Intel GPU (Windows via DirectML)
```bash
# Using pip
pip install reader
pip uninstall onnxruntime
pip install onnxruntime-directml

# Using poetry
poetry remove onnxruntime
poetry add onnxruntime-directml
```

## 🚀 Quick Start

```bash
# 1. Add a text file
echo "Hello world! This is my first audiobook." > text/hello.txt

# 2. Convert to audiobook (Neural Engine optimized)
poetry run reader convert

# 3. Listen to finished/hello_kokoro_am_michael.mp3
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
  chunk_size: 1200         # Text chunk size for processing
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
- **Model Size**: ~300MB ONNX models (auto-downloaded on first run)
- **Python**: 3.10-3.13 compatibility
- **Platforms**: macOS (Neural Engine optimized), Linux, Windows
- **Audio Quality**: 48kHz mono MP3, professional audiobook standard
- **Hardware Acceleration**:
  - Apple Silicon: CoreML (Neural Engine)
  - NVIDIA: CUDA via onnxruntime-gpu
  - AMD/Intel: DirectML on Windows
- **Performance**: Significantly faster than CPU-only solutions on Apple Silicon
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

### Models Directory Missing
**Error**: `Kokoro models not found` or `models/ directory empty`

**Solution**:
The Kokoro TTS models (~300MB) are downloaded automatically on first use. If download fails:
```bash
# Manual download
mkdir -p models/kokoro
# Models will auto-download on next run, or download from:
# https://huggingface.co/hexgrad/Kokoro-82M
```

### Neural Engine Not Detected (Apple Silicon)
**Error**: `Neural Engine not available, using CPU`

**Solution**:
- Ensure you're on Apple Silicon (M1/M2/M3 Mac)
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