"""Model download utilities for Kokoro TTS."""
import os
import urllib.request
from pathlib import Path


def get_cache_dir() -> Path:
    """Get models directory. Checks env var, models/ folder, then system cache."""
    import platform

    # Check environment variable first
    env_dir = os.getenv('AUDIOBOOK_READER_MODELS_DIR')
    if env_dir:
        custom_dir = Path(env_dir)
        custom_dir.mkdir(parents=True, exist_ok=True)
        return custom_dir

    # Check package models/ folder second
    package_models = Path(__file__).parent.parent.parent / "models"
    if package_models.exists():
        return package_models

    # Fall back to system cache
    if platform.system() == "Windows":
        cache = Path.home() / "AppData/Local/audiobook-reader/models"
    elif platform.system() == "Darwin":
        cache = Path.home() / "Library/Caches/audiobook-reader/models"
    else:
        cache = Path.home() / ".cache/audiobook-reader/models"

    cache.mkdir(parents=True, exist_ok=True)
    return cache


def download_models(
    verbose: bool = True,
    target_dir: Path = None,
    base_url: str = None
) -> bool:
    """Download Kokoro models (~310MB)."""
    from ..engines.kokoro_engine import KOKORO_MODEL_FILE, KOKORO_VOICES_FILE, KOKORO_MODEL_URL

    if base_url is None:
        base_url = KOKORO_MODEL_URL

    cache = (target_dir or get_cache_dir()) / "kokoro"
    cache.mkdir(parents=True, exist_ok=True)

    model = cache / KOKORO_MODEL_FILE
    voices = cache / KOKORO_VOICES_FILE

    if model.exists() and voices.exists():
        return True

    try:
        if verbose:
            print(f"📥 Downloading Kokoro models to {cache}")

        for name, path in [(KOKORO_MODEL_FILE, model), (KOKORO_VOICES_FILE, voices)]:
            if not path.exists():
                if verbose:
                    print(f"   {name}...", end=" ", flush=True)
                urllib.request.urlretrieve(f"{base_url}/{name}", path)
                if verbose:
                    print("✓")

        return True

    except Exception as e:
        if verbose:
            print(f"❌ Download failed: {e}")
            print(f"💡 Run: reader download models")
        return False
