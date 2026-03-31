# Advanced Features

## Chapter Management

Tiered chapter detection with three fallback levels:

1. **Marked chapters**: Structural markup from EPUB (h1-h6 tags)
2. **Heading detection**: Known section names, short isolated title lines
3. **Formatting fallback**: ALL CAPS lines with blank-line context

```bash
reader chapters extract book.epub
reader chapters extract book.pdf --output chapters.json --format json
```

## Text Stripping

Interactive chapter removal with 5-signal content classifier:

```bash
reader strip book.epub

# Selection syntax:
#   s 0, 6-8   → Strip chapters 0, 6, 7, 8
#   k 1-5      → Keep chapters 1-5 only
```

Signals: title keywords, EPUB metadata, content patterns, prose density, relative length. Front-matter gets higher sensitivity, back-matter is conservative. End preview is spoiler-protected.

## Voice Preview

```bash
reader preview af_sarah
reader preview af_sarah --text "Custom preview text"
reader preview af_sarah --output-dir voice_tests/
```

## Checkpoint Resumption

Conversions auto-checkpoint. If interrupted (crash, Ctrl+C, reboot), run the same command again to resume from where it stopped. Checkpoints are metadata-only (<1KB).

## Batch Processing

```bash
reader batch add book1.epub book2.pdf novel.txt
reader batch add --directory books/ --recursive
reader batch process --max-workers 4
reader batch status
```

## Character Voice Mapping

```bash
# Map characters to voices
reader characters add "Alice" af_sarah
reader characters add "Bob" am_michael

# Auto-detect characters from text
reader characters detect novel.txt --auto-assign

# Convert with character-aware dialogue
reader convert --characters --file novel.txt
```

## Voice Blending

Create custom voices by blending existing ones:

```bash
reader blend create narrator "af_sarah:60,af_nicole:40"
reader blend list
```

## Multi-Layer Configuration

Priority: defaults → user config → project config → CLI arguments.

**User config** (`~/.config/audiobook-reader/config.yaml`): personal defaults for all conversions.

**Project config** (`.reader.yaml` in any parent directory): per-project overrides. Configs merge — only specify what changes.

```yaml
# ~/books/fiction/.reader.yaml
tts:
  voice: am_michael
processing:
  character_voices: true
```

## Output Formats

| Format | Description |
|--------|-------------|
| MP3 | 24kHz mono, configurable bitrate (default) |
| WAV | Uncompressed PCM |
| M4A | AAC for Apple ecosystem |
| M4B | Audiobook format with chapter markers |

## Available Voices (54 across 9 languages)

- **American English** (20): af_heart, af_alloy, af_aoede, af_bella, af_jessica, af_kore, af_nicole, af_nova, af_river, af_sarah, af_sky, am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck, am_santa
- **British English** (8): bf_alice, bf_emma, bf_isabella, bf_lily, bm_daniel, bm_fable, bm_george, bm_lewis
- **Japanese** (5): jf_alpha, jf_gongitsune, jf_nezumi, jf_tebukuro, jm_kumo
- **Mandarin Chinese** (8): zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zf_xiaoyi, zm_yunjian, zm_yunxi, zm_yunxia, zm_yunyang
- **Spanish** (3): ef_dora, em_alex, em_santa
- **French** (1): ff_siwis
- **Hindi** (4): hf_alpha, hf_beta, hm_omega, hm_psi
- **Italian** (2): if_sara, im_nicola *(early-stage quality)*
- **Brazilian Portuguese** (3): pf_dora, pm_alex, pm_santa
