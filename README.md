# Reader: Text-to-Audiobook CLI

A lightweight, modular Python application that converts text files into audiobooks using AI-powered text-to-speech.

## 🎯 Phase 1: Complete CLI Foundation (~50MB)

✅ **Current features:**
- **Multiple file formats**: EPUB, PDF, TXT, Markdown, ReStructuredText
- **System TTS integration**: Voice selection, speed control, volume adjustment
- **WAV audio output**: High-quality uncompressed audio
- **Automatic chapter detection**: Smart parsing for structured content
- **Modular architecture**: Swappable components for future enhancements
- **Configuration management**: Persistent settings and preferences

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

## 🎙️ Basic Commands

```bash
# Convert all files in text/ folder
poetry run reader convert

# Convert with custom voice and speed
poetry run reader convert --voice "Samantha" --speed 1.2

# List available voices
poetry run reader voices

# Configure default settings
poetry run reader config --voice "Daniel" --speed 1.1

# View application info
poetry run reader info
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
- **WAV** (Phase 1) - Uncompressed, high quality
- **MP3, M4A, M4B** (Phase 2+) - Compressed with metadata

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