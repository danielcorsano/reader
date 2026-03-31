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

- **American English** (20): af_heart, af_alloy, af_aoede, af_bella, af_jessica, af_kore, af_nicole, af_nova, af_river, af_sarah, af_sky, am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck, am_santa
- **British English** (8): bf_alice, bf_emma, bf_isabella, bf_lily, bm_daniel, bm_fable, bm_george, bm_lewis
- **Japanese** (5): jf_alpha, jf_gongitsune, jf_nezumi, jf_tebukuro, jm_kumo
- **Mandarin Chinese** (8): zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zf_xiaoyi, zm_yunjian, zm_yunxi, zm_yunxia, zm_yunyang
- **Spanish** (3): ef_dora, em_alex, em_santa
- **French** (1): ff_siwis
- **Hindi** (4): hf_alpha, hf_beta, hm_omega, hm_psi
- **Italian** (2): if_sara, im_nicola *(early-stage quality)*
- **Brazilian Portuguese** (3): pf_dora, pm_alex, pm_santa

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
