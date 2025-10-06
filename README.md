# Reader: Neural Text-to-Audiobook CLI

A powerful Python application that converts text files into professional audiobooks using AI-powered Neural Engine acceleration and Kokoro TTS.

## ✨ Features

- **🧠 Neural Engine Optimization**: Apple Silicon (M1/M2/M3) CoreML acceleration
- **🎙️ Kokoro TTS**: 48 high-quality neural voices across 8 languages
- **📊 Real-time Visualization**: 4 progress styles including ASCII timeseries charts
- **💾 Smart Processing**: Checkpoint recovery and streaming audio assembly
- **🎭 Character Voice Mapping**: Dialogue detection with character-specific voices
- **📚 Multiple Formats**: EPUB, PDF, TXT, Markdown, ReStructuredText input
- **🎵 Professional Audio**: Optimized MP3, M4A, M4B output with metadata
- **⚡ High Performance**: 6x faster than real-time playback on Apple Silicon

## 📦 Installation

### Using pip (recommended for users)
```bash
# Default installation (Kokoro TTS + core features)
pip install reader

# With advanced NLP features (adds spacy for better dialogue detection)
pip install reader[nlp]

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
git clone https://github.com/yourusername/reader.git
cd reader

# Default installation
poetry install

# With optional extras
poetry install --extras "nlp progress-full"

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

# Fallback to system TTS (if Kokoro unavailable)
poetry run reader convert --file text/book.epub --engine pyttsx3

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

- **Dependencies**: Core packages + Kokoro TTS
- **Python**: 3.10-3.13 compatibility
- **Platforms**: macOS (Neural Engine), Linux, Windows
- **Performance**: 6x faster than real-time on Apple Silicon
- **Audio Quality**: 48kHz mono MP3, optimized for audiobooks
- **Neural Engine**: CoreML acceleration on M1/M2/M3 Macs
- **Model Size**: 82M parameters, ~300MB ONNX models

## 🎵 Audio Quality

**Kokoro TTS** (primary engine):
- ✅ Near-human quality neural voices
- ✅ 48 voices across 8 languages
- ✅ Apple Neural Engine acceleration
- ✅ Professional audiobook production

**pyttsx3** (fallback):
- ✅ Works without Kokoro models
- ✅ System TTS (macOS, Windows, Linux)
- ⚠️ Lower quality, suitable for testing

---

**Ready to create your first audiobook?** Check out the **[Usage Guide](docs/USAGE.md)** for step-by-step instructions!