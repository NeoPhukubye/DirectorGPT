"""Project state management for DirectorGPT."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import json


class ProductionPhase(Enum):
    DEVELOPMENT = "development"
    PRE_PRODUCTION = "pre_production"
    PRODUCTION = "production"
    POST_PRODUCTION = "post_production"
    COMPLETED = "completed"


@dataclass
class ProjectConfig:
    project_name: str
    output_dir: Path
    fps: int = 24
    resolution: tuple[int, int] = (1920, 1080)
    enable_image_generation: bool = False
    enable_video_generation: bool = False
    enable_audio_generation: bool = False
    llm_model: str = "gpt-4"
    temp_dir: Optional[Path] = None

    def __post_init__(self):
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.temp_dir:
            self.temp_dir = Path(self.temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class ProjectState:
    config: ProjectConfig
    phase: ProductionPhase = ProductionPhase.DEVELOPMENT
    current_scene: int = 0
    current_shot: int = 0
    agent_messages: list[dict] = field(default_factory=list)
    artifacts: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def transition_to(self, phase: ProductionPhase):
        self.phase = phase

    def add_message(self, agent: str, message: str, message_type: str = "info"):
        self.agent_messages.append({
            "agent": agent,
            "message": message,
            "type": message_type,
            "phase": self.phase.value,
        })

    def add_artifact(self, name: str, path: Path):
        self.artifacts[name] = path

    def add_error(self, error: str):
        self.errors.append(error)

    def save_state(self):
        state_file = self.config.output_dir / "project_state.json"
        state_data = {
            "phase": self.phase.value,
            "current_scene": self.current_scene,
            "current_shot": self.current_shot,
            "agent_messages": self.agent_messages,
            "artifacts": {k: str(v) for k, v in self.artifacts.items()},
            "errors": self.errors,
        }
        state_file.write_text(json.dumps(state_data, indent=2))

    @classmethod
    def load_state(cls, config: ProjectConfig) -> "ProjectState":
        state_file = config.output_dir / "project_state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text())
            state = cls(config=config)
            state.phase = ProductionPhase(data["phase"])
            state.current_scene = data["current_scene"]
            state.current_shot = data["current_shot"]
            state.agent_messages = data["agent_messages"]
            state.artifacts = {k: Path(v) for k, v in data["artifacts"].items()}
            state.errors = data["errors"]
            return state
        return cls(config=config)
