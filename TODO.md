# TODO

## In Progress

### Misaki G2P Integration (dev branch)
- [x] Created `reader/text_processing/phonemizer.py` — G2P wrapper with graceful fallback
- [x] Wired into `neural_processor.py` and `kokoro_engine.py` with `is_phonemes` support
- [x] Added `--no-g2p` CLI flag
- [x] Added misaki as optional dep in pyproject.toml (`g2p-en` extra)
- [x] Voice quality grades added to all 6 docs from upstream VOICES.md
- [x] Strip+convert workflow added to API.md and KOKORO_SETUP.md
- [x] **RESOLVED**: espeak conflict fixed — removed espeak fallback, install misaki without `[en]` extra to avoid pulling `phonemizer` (conflicts with `phonemizer-fork`). Added `num2words` and `spacy` as explicit optional deps instead.
- [x] Test G2P end-to-end with misaki installed — all passing (phonemization, synthesis, unknown word fallback)
- [x] Update docs to mention G2P feature and `--no-g2p` flag (USAGE.md, ADVANCED_FEATURES.md, KOKORO_SETUP.md)
- [ ] Version bump for next release

## Backlog

- Evaluate changing default voice from am_michael (C+) to af_heart (A) or af_bella (A-)
- CHANGELOG links point to GitHub release tags but no GitHub releases exist — consider removing or creating releases
