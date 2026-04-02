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

## G2P Pronunciation Enhancement

Optional grapheme-to-phoneme preprocessing using [misaki](https://github.com/hexgrad/misaki). Improves pronunciation of abbreviations, numbers, and homographs by converting text to IPA phonemes before Kokoro synthesis.

```bash
# Install
pip install audiobook-reader[g2p-en]

# Activates automatically when installed
reader convert --file book.epub

# Disable for a specific conversion
reader convert --file book.epub --no-g2p
```

Unknown words that misaki can't resolve are passed through as original text for Kokoro's internal espeak to handle — no pronunciation gaps.

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

Grades from [Kokoro-82M VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) reflect training data quality and quantity.

**Top voices by grade:** af_heart (A), af_bella (A-), af_nicole (B-), bf_emma (B-), ff_siwis (B-)

**American English** (20 voices):

| Voice | Gender | Grade | Notes |
|-------|--------|-------|-------|
| af_heart | F | A | Best overall quality |
| af_bella | F | A- | High quality, long training data |
| af_nicole | F | B- | Long training data |
| af_aoede | F | C+ | |
| af_kore | F | C+ | |
| af_sarah | F | C+ | |
| af_alloy | F | C | |
| af_nova | F | C | |
| af_jessica | F | D | |
| af_river | F | D | |
| af_sky | F | C- | Very short training data |
| am_michael | M | C+ | Default voice |
| am_fenrir | M | C+ | |
| am_puck | M | C+ | |
| am_echo | M | D | |
| am_eric | M | D | |
| am_liam | M | D | |
| am_onyx | M | D | |
| am_adam | M | F+ | Low quality training data |
| am_santa | M | D- | Very short training data |

**British English** (8): bf_emma (F, B-), bf_isabella (F, C), bf_alice (F, D), bf_lily (F, D), bm_fable (M, C), bm_george (M, C), bm_lewis (M, D+), bm_daniel (M, D)

**Japanese** (5): jf_alpha (F, C+), jf_gongitsune (F, C), jf_tebukuro (F, C), jf_nezumi (F, C-), jm_kumo (M, C-)

**Mandarin Chinese** (8): zf_xiaobei (F, D), zf_xiaoni (F, D), zf_xiaoxiao (F, D), zf_xiaoyi (F, D), zm_yunjian (M, D), zm_yunxi (M, D), zm_yunxia (M, D), zm_yunyang (M, D)

**Spanish** (3): ef_dora (F), em_alex (M), em_santa (M)

**French** (1): ff_siwis (F, B-)

**Hindi** (4): hf_alpha (F, C), hf_beta (F, C), hm_omega (M, C), hm_psi (M, C)

**Italian** (2): if_sara (F, C), im_nicola (M, C)

**Brazilian Portuguese** (3): pf_dora (F), pm_alex (M), pm_santa (M)
