# Reader Examples

## Convert a Single File

```bash
reader convert --file mybook.epub
# Output: ~/Downloads/mybook_am_michael_sp1p1.mp3
```

## Choose a Voice

```bash
# List all 54 voices across 9 languages
reader voices

# Filter by language or gender
reader voices --language it
reader voices --gender female

# Convert with a specific voice
reader convert --file book.epub --voice af_sarah
reader convert --file book.epub --voice bf_emma
reader convert --file book.epub --voice im_nicola  # Italian
```

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

## Strip and Convert

```bash
# Strip unwanted chapters (TOC, bibliography, index, etc.)
reader strip "Ethics.epub"
# → Auto-detects non-content, lets you refine, saves _stripped.epub
# → Offers to convert immediately

# Works with PDFs too
reader strip textbook.pdf
```

## Character Voice Mapping

```bash
# Auto-detect characters and assign voices
reader characters detect novel.txt --auto-assign

# Or manually map characters
reader characters add "Alice" af_sarah
reader characters add "Bob" am_michael

# Convert with character voices
reader convert --characters --file novel.txt
```

## Voice Blending

```bash
# Create a custom blended voice
reader blend create narrator "af_sarah:60,af_nicole:40"

# Use it
reader convert --voice "af_sarah:60,af_nicole:40" --file book.epub
```

## Batch Processing

```bash
reader convert --file book1.epub --output-dir /audiobooks
reader convert --file book2.pdf --output-dir /audiobooks
reader convert --file story.txt --output-dir /audiobooks
```

## Configuration

```bash
# Save preferred settings
reader config --voice am_michael --speed 1.0 --format mp3

# Override per-conversion
reader convert --voice af_sarah --file book.epub

# Per-project config: create .reader.yaml in any directory
# All conversions in that directory tree inherit those settings
```

## Debug Mode

```bash
# See Neural Engine status and processing details
reader convert --debug --file book.epub
```
