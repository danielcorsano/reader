# Reader Documentation

This directory contains comprehensive documentation for the Reader audiobook generation CLI.

## Quick Start
- **[USAGE.md](USAGE.md)** - Complete usage guide and command reference
- **[EXAMPLES.md](EXAMPLES.md)** - Step-by-step examples and workflows

## Setup Guides
- **[KOKORO_SETUP.md](KOKORO_SETUP.md)** - Neural TTS setup for Phase 2/3 features

## Advanced Features
- **[PHASE3_FEATURES.md](PHASE3_FEATURES.md)** - Professional audiobook production features

## Getting Started

1. **Install dependencies:** `poetry install`
2. **Download Kokoro models:** See [KOKORO_SETUP.md](KOKORO_SETUP.md)
3. **Add text files** to the `text/` folder
4. **Convert to audiobook:** `poetry run reader convert`
5. **Find results** in the `finished/` folder

For detailed instructions, see [USAGE.md](USAGE.md).