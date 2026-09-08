"""Tests for project state management."""

import tempfile
from pathlib import Path

from director_gpt.models.project import (
    ProductionPhase,
    ProjectConfig,
    ProjectState,
)


def test_project_config_creates_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_output"
        config = ProjectConfig(
            project_name="test",
            output_dir=output_dir,
        )
        assert output_dir.exists()
        assert config.fps == 24
        assert config.resolution == (1920, 1080)


def test_project_state_add_message():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ProjectConfig(
            project_name="test",
            output_dir=Path(tmpdir) / "output",
        )
        state = ProjectState(config=config)
        state.add_message("Director", "Starting production")
        assert len(state.agent_messages) == 1
        assert state.agent_messages[0]["agent"] == "Director"
        assert state.agent_messages[0]["message"] == "Starting production"
        assert state.agent_messages[0]["phase"] == "development"


def test_project_state_transition():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ProjectConfig(
            project_name="test",
            output_dir=Path(tmpdir) / "output",
        )
        state = ProjectState(config=config)
        assert state.phase == ProductionPhase.DEVELOPMENT
        state.transition_to(ProductionPhase.PRE_PRODUCTION)
        assert state.phase == ProductionPhase.PRE_PRODUCTION


def test_project_state_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "output"
        config = ProjectConfig(
            project_name="test",
            output_dir=output_dir,
        )
        state = ProjectState(config=config)
        state.add_message("Director", "Test message")
        state.add_artifact("script", output_dir / "script.json")
        state.save_state()

        # Load state
        loaded = ProjectState.load_state(config)
        assert loaded.phase == state.phase
        assert len(loaded.agent_messages) == len(state.agent_messages)
        assert loaded.agent_messages[0]["message"] == "Test message"
        assert "script" in loaded.artifacts


def test_project_state_add_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ProjectConfig(
            project_name="test",
            output_dir=Path(tmpdir) / "output",
        )
        state = ProjectState(config=config)
        state.add_error("Something went wrong")
        assert len(state.errors) == 1
        assert state.errors[0] == "Something went wrong"
