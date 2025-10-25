"""Model download utilities for Kokoro TTS."""
import urllib.request
from pathlib import Path


def get_cache_dir() -> Path:
    """Get models directory. Checks models/ folder first, then system cache."""
    import platform

    # Check package models/ folder first
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
    base_url: str = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
) -> bool:
    """Download Kokoro models (~310MB)."""
    cache = (target_dir or get_cache_dir()) / "kokoro"
    cache.mkdir(parents=True, exist_ok=True)

    model = cache / "kokoro-v1.0.onnx"
    voices = cache / "voices-v1.0.bin"

    if model.exists() and voices.exists():
        return True

    try:
        if verbose:
            print(f"📥 Downloading Kokoro models to {cache}")

        for name, path in [("kokoro-v1.0.onnx", model), ("voices-v1.0.bin", voices)]:
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
