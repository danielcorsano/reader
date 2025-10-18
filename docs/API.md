# Programmatic API

Reader provides a Python API for programmatic audiobook generation in scripts, notebooks, and applications.

## Installation

```bash
pip install audiobook-reader
```

## Quick Start

### Simple Conversion

```python
import reader

# Convert with defaults (outputs to ~/Downloads/)
output = reader.convert("mybook.epub")
print(f"Audiobook created: {output}")
# Output: Audiobook created: /Users/name/Downloads/mybook_kokoro_am_michael.mp3
```

### Customized Conversion

```python
import reader

# Convert with custom settings
output = reader.convert(
    "mybook.epub",
    voice="af_sarah",           # Female voice
    speed=1.2,                  # 20% faster
    output_format="mp3",        # MP3 format
    output_dir="same"           # Output next to source file
)
```

### List Available Voices

```python
import reader

voices = reader.list_voices()
for voice_id, info in voices.items():
    print(f"{voice_id}: {info['gender']}, {info['language']}")
```

## Class-Based API

For more control, use the `Reader` class:

```python
from reader import Reader

# Initialize reader
r = Reader()

# Convert file
output = r.convert(
    "mybook.epub",
    voice="am_michael",
    speed=1.0,
    character_voices=True,      # Enable character voice mapping
    progress_style="timeseries" # Real-time visualization
)
```

## API Reference

### `reader.convert()`

```python
def convert(
    file_path: str,
    voice: Optional[str] = None,
    speed: Optional[float] = None,
    output_format: Optional[str] = None,
    character_voices: bool = False,
    character_config: Optional[str] = None,
    checkpoint_interval: int = 50,
    progress_style: str = "simple",
    debug: bool = False,
    output_dir: Optional[str] = None
) -> Path
```

**Parameters:**
- **file_path** (str): Path to input file (EPUB, PDF, TXT, MD, RST). For other formats like DOCX, MOBI, or HTML, use [convertext](https://pypi.org/project/convertext/) to convert first.
- **voice** (str, optional): Voice ID (e.g., 'am_michael', 'af_sarah'). Defaults to config.
- **speed** (float, optional): Speech speed multiplier (0.5-2.0). Default: 1.0
- **output_format** (str, optional): Audio format ('mp3', 'wav', 'm4a', 'm4b'). Default: 'mp3'
- **character_voices** (bool): Enable character-specific voices for dialogue. Default: False
- **character_config** (str, optional): Path to character voice mapping YAML file
- **checkpoint_interval** (int): Save progress every N chunks. Default: 50
- **progress_style** (str): Progress display ('simple', 'tqdm', 'rich', 'timeseries'). Default: 'simple'
- **debug** (bool): Enable debug logging. Default: False
- **output_dir** (str, optional): Output directory ('downloads', 'same', or explicit path). Default: 'downloads' (~/Downloads/)

**Returns:**
- **Path**: Path to generated audiobook file in specified output directory

**Raises:**
- **FileNotFoundError**: If input file doesn't exist
- **ValueError**: If invalid parameters provided
- **RuntimeError**: If conversion fails

### `reader.list_voices()`

```python
def list_voices() -> Dict[str, Any]
```

**Returns:**
- Dictionary mapping voice IDs to voice information:
  ```python
  {
      'am_michael': {
          'gender': 'Male',
          'language': 'American English',
          'sample_rate': 24000
      },
      ...
  }
  ```

### `Reader` Class

```python
class Reader:
    def __init__(self)
    def convert(...) -> Path
    def list_voices() -> Dict[str, Any]
```

Same parameters as module-level functions.

## Use Cases

### Jupyter Notebook

```python
from reader import Reader
from IPython.display import Audio

# Convert book
r = Reader()
output = r.convert("book.epub", progress_style="tqdm")

# Play in notebook
Audio(str(output))
```

### Batch Processing

```python
from reader import Reader
from pathlib import Path

r = Reader()

# Convert all EPUBs in a directory
for epub in Path("books/").glob("*.epub"):
    try:
        output = r.convert(
            str(epub),
            voice="af_sarah",
            progress_style="simple"
        )
        print(f"✓ {epub.name} -> {output.name}")
    except Exception as e:
        print(f"✗ {epub.name}: {e}")
```

### Custom Voice Pipeline

```python
from reader import Reader

r = Reader()

# Create audiobook with character voices
output = r.convert(
    "plato_republic.epub",
    character_voices=True,
    character_config="characters.yaml",
    speed=1.1,
    progress_style="rich",
    output_dir="/audiobooks"  # Custom output location
)
```

### Integration with Other Tools

```python
import reader
from pydub import AudioSegment

# Generate audiobook
output = reader.convert("chapter1.txt", output_format="wav")

# Post-process with pydub
audio = AudioSegment.from_wav(str(output))
audio = audio.normalize()  # Normalize volume
audio.export("chapter1_normalized.mp3", format="mp3", bitrate="64k")
```

## Error Handling

```python
import reader
from pathlib import Path

try:
    output = reader.convert(
        "mybook.epub",
        voice="af_sarah",
        speed=1.2
    )
    print(f"Success: {output}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Invalid parameter: {e}")
except RuntimeError as e:
    print(f"Conversion failed: {e}")
```

## Advanced Features

### Resume from Checkpoint

Conversions automatically save checkpoints every 50 chunks. If interrupted, simply run the same command again:

```python
import reader

# First run - processes 100/500 chunks then crashes
reader.convert("largebook.epub")

# Second run - automatically resumes from chunk 100
reader.convert("largebook.epub")
```

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import reader

output = reader.convert("book.epub", debug=True)
# Writes detailed logs to checkpoint_debug.log
```

### Progress Styles

Choose different progress visualizations:

```python
import reader

# Simple text output (best for scripts)
reader.convert("book.epub", progress_style="simple")

# TQDM progress bar (requires: pip install tqdm)
reader.convert("book.epub", progress_style="tqdm")

# Rich enhanced display (requires: pip install rich)
reader.convert("book.epub", progress_style="rich")

# Real-time charts (requires: pip install plotext)
reader.convert("book.epub", progress_style="timeseries")
```

## Configuration

The API respects your Reader configuration:

```bash
# Set defaults via CLI
reader config

# Then use defaults in API
import reader
reader.convert("book.epub")  # Uses configured voice/format/speed
```

## File Locations

### Temporary Files
- `/tmp/audiobook-reader-{session}/` - Working files (auto-cleaned on exit)
- Session-specific workspace, isolated from your files

### Persistent Data
- `~/.cache/audiobook-reader/models/` - TTS models (~310MB, shared)
- `~/.config/audiobook-reader/` - Configuration and character mappings

### Output Files
- `~/Downloads/` (default) - Configurable with `output_dir` parameter
- Options: `"downloads"`, `"same"` (next to source), or custom path

## Notes

- All conversions use checkpoint/resume for reliability
- Output files placed in configured output directory
- Temporary files cleaned up automatically on exit
- Supports Apple Silicon Neural Engine acceleration
- Handles non-English text (Greek, Cyrillic, Arabic, etc.)
- No directory pollution - only final audiobooks in output location
