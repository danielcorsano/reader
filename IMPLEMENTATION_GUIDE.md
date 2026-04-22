# Implementation Guide

Technical decisions, patterns, and lessons learned in the audiobook-reader project.

## Misaki G2P Integration

### What It Does

Optional grapheme-to-phoneme preprocessing using [misaki](https://github.com/hexgrad/misaki). Converts text to IPA phonemes before passing to Kokoro, improving pronunciation of abbreviations, numbers, and homographs.

### Architecture

```
Text chunk → Phonemizer (misaki) → IPA phonemes → Kokoro (is_phonemes=True) → Audio
         ↘ (if misaki unavailable) → raw text → Kokoro (normal path) → Audio
```

- **Singleton pattern**: `get_phonemizer()` returns a single shared instance
- **Lazy loading**: misaki modules loaded on first use per language, not at import time
- **Graceful fallback**: if misaki isn't installed, text passes through unchanged — zero impact on existing behavior
- **CLI opt-out**: `--no-g2p` flag disables phonemization even when misaki is available

### The espeak Conflict and Resolution

**Problem**: Two conflicts between `misaki[en]` and `kokoro-onnx`:

1. **espeak initialization conflict**: `misaki`'s `espeak.EspeakFallback()` configures the native espeak library differently than kokoro-onnx expects, causing `EspeakWrapper.set_data_path` to be missing.

2. **Package namespace conflict**: `misaki[en]` extra pulls in `phonemizer` (the original, v3.3.0), which overwrites the `phonemizer` Python namespace used by `phonemizer-fork` (v3.3.2) that kokoro-onnx depends on. Both packages install into the same `phonemizer` module path — the original one lacks the `EspeakWrapper` class that kokoro-onnx needs.

**Root cause**: `misaki[en]` declares `phonemizer` (not `phonemizer-fork`) as a dependency. These are separate PyPI packages that occupy the same Python namespace, and the original lacks kokoro-onnx's required APIs.

**Options considered**:
1. Pin compatible versions — not possible, they're different packages
2. Control import order — doesn't help when the wrong package is installed
3. **Skip espeak fallback + install misaki without [en] extra** — chosen solution
4. Force kokoro to init before misaki — doesn't fix the namespace collision
5. Wait for upstream fix — indefinite delay

**Solution (two parts)**:

1. Initialize misaki G2P with `fallback=None` — prevents misaki from importing its espeak module entirely.

2. Install `misaki` **without** the `[en]` extra in pyproject.toml. The `[en]` extra's only unique dep is `phonemizer` (which conflicts). The other deps (`num2words`, `spacy`) are added explicitly as separate optional dependencies in the `g2p-en` extra group. The `misaki.en` module itself is part of base misaki.

**Unknown word handling**: With `fallback=None`, words not in misaki's lexicon get `phonemes=None`. The `_phonemize_safe()` method catches this, replaces `None` phonemes with the original text, and passes the mixed result to Kokoro. Kokoro's internal espeak handles the non-phonemized words — no pronunciation gaps.

**Why this works**: Kokoro already has a complete espeak pipeline internally. The espeak fallback in misaki was redundant in this integration. And by not installing `phonemizer` (only `phonemizer-fork` via kokoro-onnx), the namespace conflict disappears.

### Key Files

- `reader/text_processing/phonemizer.py` — G2P wrapper, singleton, per-language lazy init
- `reader/batch/neural_processor.py` — calls phonemizer before synthesis
- `reader/engines/kokoro_engine.py` — `synthesize()` accepts `is_phonemes` flag
- `reader/cli.py` — `--no-g2p` CLI flag
