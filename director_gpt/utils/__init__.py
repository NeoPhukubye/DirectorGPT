"""Utility functions and configuration helpers."""

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, cast


def get_output_dir(name: str) -> Path:
    """Get or create output directory for a project."""
    output_dir = Path("./output") / name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available on the system."""
    return shutil.which("ffmpeg") is not None


def get_env_or_prompt(var_name: str, prompt_text: str) -> str | None:
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


def safe_import(module_name: str, package_name: str | None = None) -> tuple[Any | None, str | None]:
    """Safely import an optional dependency, returning (module, error_message)."""
    package_name = package_name or module_name
    try:
        module = __import__(module_name, fromlist=[""])
        return module, None
    except ImportError:
        return None, (
            f"Optional dependency '{package_name}' is not installed. "
            f"Install it with: pip install {package_name}"
        )


def clean_json_text(raw: str) -> str:
        """Strip markdown code fences from LLM output before JSON parsing."""
        if not raw or not isinstance(raw, str):
            return ""
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json") :]
        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```") :]
        cleaned = cleaned.removesuffix("```")
        return cleaned.strip()


def extract_json_from_text(text: str) -> str | None:
        """Extract the first JSON object found in a text string.

        Returns the JSON substring or None if no valid JSON braces are found.
        """
        if not text or not isinstance(text, str):
            return None
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        return text[start : end + 1]


def parse_llm_json(text: str) -> dict | None:
        """Parse JSON from LLM output, handling code fences and embedded text.

        Falls back to brace-matching extraction if direct parsing fails.
        """
        if not text or not isinstance(text, str):
            return None
        candidates = [clean_json_text(text), extract_json_from_text(text)]
        for candidate in candidates:
            if not candidate:
                continue
            try:
                return cast(dict, json.loads(candidate))
            except json.JSONDecodeError:
                continue
        return None


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a numeric value to a range."""
    return max(low, min(value, high))


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return slug.strip("-")


def ensure_dir(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_api_key(provider: str) -> str | None:
    """Get API key for a provider from environment variables.

    Supports both ``<PROVIDER>_API_KEY`` and ``<PROVIDER>_API_SECRET``.
    """
    provider = provider.lower()
    for suffix in ("API_KEY", "API_SECRET"):
        key = os.environ.get(f"{provider.upper()}_{suffix}")
        if key:
            return key
    return None
