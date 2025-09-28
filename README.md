# Reader: Text-to-Audiobook CLI

A powerful, modular Python application that converts text files into audiobooks using AI-powered text-to-speech engines.

## ✨ **All Phases Implemented**

✅ **Phase 1: Core Foundation**
- Multiple file formats: EPUB, PDF, TXT, Markdown, ReStructuredText
- System TTS integration with voice selection and speed control
- Automatic chapter detection and smart parsing

✅ **Phase 2: Neural TTS + Emotion Analysis** 
- **Kokoro TTS**: 48 high-quality neural voices across 8 languages
- **Emotion analysis**: Automatic prosody based on text sentiment
- **Character voice mapping**: Different voices for different characters
- **Voice blending**: Create custom mixed voices

✅ **Phase 3: Professional Production**
- **Advanced audio formats**: MP3, M4A, M4B with metadata
- **Dialogue detection**: Smart character voice assignment
- **Optimized for audiobooks**: Smaller file sizes, better quality
- **Batch processing**: Robust processing with checkpoint recovery

## 🚀 Quick Start

```bash
# 1. Install dependencies
poetry install

# 2. Add a text file
echo "Hello world! This is my first audiobook." > text/hello.txt

# 3. Convert to audiobook
poetry run reader convert

# 4. Listen to audio/hello.wav
```

## 📖 Documentation

- **[Usage Guide](docs/USAGE.md)** - Complete command reference and workflows
- **[Examples](docs/EXAMPLES.md)** - Real-world examples and use cases
- **[Architecture](docs/ARCHITECTURE.md)** - Technical design and development guide

## 🎙️ Command Reference

### Basic Conversion
```bash
# Convert single file (temporary overrides, won't save to config)
poetry run reader convert --file text/book.epub --voice am_michael --engine kokoro

# Convert with specific processing level
poetry run reader convert --processing-level phase3 --engine kokoro

# Fast conversion for large books
poetry run reader convert --engine pyttsx3 --processing-level phase1

# Batch processing with checkpoints (for very large books)
poetry run reader convert --batch-mode --checkpoint-interval 100
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
- **MP3** (default) - Optimized for audiobooks, ~4-5x smaller than WAV
- **WAV** - Uncompressed, high quality  
- **M4A, M4B** (Phase 3) - Professional audiobook formats with metadata

## 🏗️ Project Structure

```
reader/
├── text/                   # 📂 Input files (your books)
├── audio/                  # 🔊 Generated audiobooks  
├── config/                 # ⚙️ Configuration files
├── docs/                   # 📚 Documentation
└── reader/
    ├── interfaces/         # 🔌 Abstract base classes
    ├── engines/           # 🎙️ TTS implementations
    ├── parsers/           # 📖 File format parsers
    └── cli.py             # 💻 Command-line interface
```

## 🔮 Roadmap

### Phase 2: Enhanced TTS + Smart Acting (~300MB)
- **Kokoro TTS**: 48 neural voices across 8 languages
- **Voice blending**: Create custom character voices  
- **Emotion detection**: VADER sentiment → automatic prosody
- **Smart acting**: Punctuation-based emphasis and pacing

### Phase 3: Professional Production (~350MB)
- **Dialogue detection**: Character voice assignment
- **Context analysis**: Scene-appropriate narration
- **M4B export**: Professional audiobook format with chapters
- **Batch processing**: Queue management and voice preview

## 🎨 Example Workflows

### Simple Book Conversion
```bash
# Add your book
cp "My Novel.epub" text/

# Convert with preferred voice
poetry run reader convert --voice "Samantha"

# Result: audio/My Novel.wav
```

### Voice Comparison
```bash
# Test different voices on same content
poetry run reader convert --voice "Daniel" --file text/sample.txt
poetry run reader convert --voice "Samantha" --file text/sample.txt
poetry run reader convert --voice "Alex" --file text/sample.txt

# Compare audio/sample.wav outputs
```

### Batch Processing
```bash
# Add multiple books
cp book1.epub book2.pdf story.txt text/

# Set default voice and convert all
poetry run reader config --voice "Daniel" --speed 1.1
poetry run reader convert

# Results: audio/book1.wav, audio/book2.wav, audio/story.wav
```

## ⚙️ Configuration

Settings are saved to `config/settings.yaml`:

```yaml
tts:
  engine: pyttsx3
  voice: "Samantha"        # Default voice
  speed: 1.1               # Speech rate multiplier  
  volume: 1.0              # Volume level
audio:
  format: wav              # Output format (Phase 1)
  add_metadata: false      # Metadata support (Phase 2+)
processing:
  chunk_size: 1000         # Text chunk size for processing
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

- **Dependencies**: 6 core packages (~50MB total)
- **Python**: 3.9+ compatibility
- **Platforms**: macOS, Linux, Windows
- **Performance**: ~1x real-time conversion
- **Quality**: 16-bit WAV, 22kHz sample rate

## 🎵 Audio Quality Notes

**Phase 1** uses system TTS engines (macOS Voices, Windows SAPI, Linux espeak):
- ✅ Fast, reliable, offline
- ⚠️ Synthetic quality (suitable for personal use)

**Phase 2+** will add neural TTS:
- ✅ Near-human quality voices
- ✅ Emotion and emphasis control
- ✅ Professional audiobook production

---

**Ready to create your first audiobook?** Check out the **[Usage Guide](docs/USAGE.md)** for step-by-step instructions!