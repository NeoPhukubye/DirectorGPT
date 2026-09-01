"""Utility functions and configuration helpers."""

import os
from pathlib import Path
from typing import Optional


def get_output_dir(name: str) -> Path:
    """Get or create output directory for a project."""
    output_dir = Path("./output") / name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available on the system."""
    import shutil
    return shutil.which("ffmpeg") is not None


def get_env_or_prompt(var_name: str, prompt_text: str) -> Optional[str]:
    """Get value from environment or prompt user."""
    value = os.environ.get(var_name)
    if value:
        return value
    try:
        return input(f"{prompt_text}: ")
    except (EOFError, KeyboardInterrupt):
        return None


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    frames = int((seconds % 1) * 24)
    return f"{mins}:{secs:02d}:{frames:02d}"
