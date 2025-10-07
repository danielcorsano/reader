"""First-run setup and validation utilities."""
import shutil
import sys
from pathlib import Path
from typing import Tuple, List


def check_ffmpeg() -> Tuple[bool, str]:
    """Check if FFmpeg is installed."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return True, f"FFmpeg found at {ffmpeg_path}"

    error_msg = """
❌ FFmpeg not found

FFmpeg is required for audio conversion. Please install:

macOS:
  brew install ffmpeg

Ubuntu/Debian:
  sudo apt-get install ffmpeg

Windows:
  choco install ffmpeg
  or download from https://ffmpeg.org/download.html
"""
    return False, error_msg


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10 and version.minor < 14:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"

    error_msg = f"""
❌ Python version incompatible

Found: Python {version.major}.{version.minor}.{version.micro}
Required: Python 3.10-3.13

Please upgrade your Python version.
"""
    return False, error_msg


def ensure_directories(base_path: Path) -> List[Path]:
    """Ensure all required directories exist."""
    required_dirs = [
        base_path / "text",
        base_path / "audio",
        base_path / "finished",
        base_path / "config",
        base_path / "models",
    ]

    created = []
    for directory in required_dirs:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(directory)

    return created


def validate_environment(base_path: Path, show_warnings: bool = True) -> bool:
    """
    Validate the environment for reader.

    Returns True if all critical checks pass, False otherwise.
    """
    all_good = True

    # Check Python version
    py_ok, py_msg = check_python_version()
    if not py_ok:
        print(py_msg)
        all_good = False
    elif show_warnings:
        print(f"✅ {py_msg}")

    # Check FFmpeg
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg()
    if not ffmpeg_ok:
        print(ffmpeg_msg)
        all_good = False
    elif show_warnings:
        print(f"✅ {ffmpeg_msg}")

    # Ensure directories
    created = ensure_directories(base_path)
    if created and show_warnings:
        print(f"✅ Created directories: {', '.join(d.name for d in created)}")

    return all_good


def first_run_setup(base_path: Path) -> bool:
    """
    Perform first-run setup.

    Returns True if setup successful, False otherwise.
    """
    print("🚀 Reader First-Run Setup")
    print("=" * 50)

    success = validate_environment(base_path, show_warnings=True)

    if success:
        print("\n✅ Setup complete! Ready to create audiobooks.")
        print("\n📚 Quick Start:")
        print("  1. Add a text file to the text/ directory")
        print("  2. Run: reader convert")
        print("  3. Find your audiobook in finished/")
        print("\n💡 Tip: Run 'reader info' for more information")
    else:
        print("\n❌ Setup incomplete. Please fix the errors above.")

    return success
