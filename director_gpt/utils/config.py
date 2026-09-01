"""Configuration management for DirectorGPT."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class ImageGenConfig:
    provider: str = "dall-e-3"
    api_key: Optional[str] = None
    size: str = "1920x1080"
    quality: str = "hd"


@dataclass
class AudioConfig:
    provider: str = "elevenlabs"
    api_key: Optional[str] = None
    voice_id: Optional[str] = None
    sample_rate: int = 44100


@dataclass
class VideoConfig:
    provider: str = "runway"
    api_key: Optional[str] = None
    fps: int = 24
    resolution: tuple[int, int] = (1920, 1080)


class Config:
    """Main configuration class."""

    def __init__(self, config_path: Optional[Path] = None):
        self.llm = LLMConfig()
        self.image_gen = ImageGenConfig()
        self.audio = AudioConfig()
        self.video = VideoConfig()
        self.output_dir = Path("./output")

        if config_path and config_path.exists():
            self.load_from_file(config_path)

    def load_from_file(self, path: Path):
        """Load configuration from JSON file."""
        data = json.loads(path.read_text())

        if "llm" in data:
            self.llm = LLMConfig(**data["llm"])
        if "image_gen" in data:
            self.image_gen = ImageGenConfig(**data["image_gen"])
        if "audio" in data:
            self.audio = AudioConfig(**data["audio"])
        if "video" in data:
            self.video = VideoConfig(**data["video"])
        if "output_dir" in data:
            self.output_dir = Path(data["output_dir"])

    def save_to_file(self, path: Path):
        """Save configuration to JSON file."""
        data = {
            "llm": self.llm.__dict__,
            "image_gen": self.image_gen.__dict__,
            "audio": self.audio.__dict__,
            "video": self.video.__dict__,
            "output_dir": str(self.output_dir),
        }
        path.write_text(json.dumps(data, indent=2))
