"""Tests for the DirectorAgent orchestrator."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from director_gpt.director import DirectorAgent
from director_gpt.models.project import ProjectConfig, ProjectState


def make_state() -> ProjectState:
    tmpdir = tempfile.mkdtemp()
    config = ProjectConfig(
        project_name="test",
        output_dir=Path(tmpdir) / "output",
    )
    return ProjectState(config=config)


def test_director_initialization():
    """DirectorAgent should initialize with all sub-agents."""
    state = make_state()
    director = DirectorAgent(state)
    assert director.screenwriter is not None
    assert director.casting is not None
    assert director.sound is not None
    assert director.editor is not None
    assert len(director.agents) == 4


def test_director_produce_film_rule_based():
    """DirectorAgent should produce a film using rule-based generation."""
    state = make_state()
    director = DirectorAgent(state)
    # Mock the editor's assemble_film to avoid FFmpeg dependency
    with patch.object(
        director.editor,
        "assemble_film",
        return_value=str(state.config.output_dir / "final_cut.mp4"),
    ):
        script = director.produce_film(
            prompt="A detective investigates a mystery",
            title="Test Film",
            genre="drama",
            target_duration=60.0,
        )
    assert script.title == "Test Film"
    assert script.genre == "drama"
    assert len(script.scenes) > 0
    assert len(script.characters) > 0
    assert len(script.soundtrack) > 0


def test_director_produce_film_with_llm():
    """DirectorAgent should use LLM client when provided."""
    state = make_state()
    mock_llm = MagicMock()
    mock_llm.generate.return_value = """```json
    {
        "characters": [{"name": "Hero", "description": "Brave", "visual_prompt": "heroic"}],
        "scenes": [{
            "scene_number": 1,
            "title": "Scene 1",
            "location": "castle",
            "time_of_day": "night",
            "description": "Hero enters",
            "emotional_tone": "tense",
            "characters": ["Hero"],
            "environment_prompt": "dark castle",
            "shots": [{
                "shot_number": 1,
                "shot_type": "wide",
                "description": "Establishing shot",
                "duration_seconds": 5.0,
                "camera_movement": "pan",
                "visual_prompt": "wide shot",
                "characters": ["Hero"],
                "emotional_tone": "tense"
            }]
        }]
    }
    ```"""
    director = DirectorAgent(state, llm_client=mock_llm)
    # Mock the editor's assemble_film to avoid FFmpeg dependency
    with patch.object(
        director.editor,
        "assemble_film",
        return_value=str(state.config.output_dir / "final_cut.mp4"),
    ):
        script = director.produce_film(
            prompt="A hero saves the day",
            title="Hero Film",
            genre="action",
            target_duration=30.0,
        )
    assert script.title == "Hero Film"
    assert len(script.scenes) == 1
    assert script.scenes[0].shots[0].shot_type.value == "wide"


def test_director_get_production_report():
    """DirectorAgent should return a production report."""
    state = make_state()
    director = DirectorAgent(state)
    # Mock the editor's assemble_film to avoid FFmpeg dependency
    with patch.object(
        director.editor,
        "assemble_film",
        return_value=str(state.config.output_dir / "final_cut.mp4"),
    ):
        director.produce_film(
            prompt="A test story",
            title="Report Test",
            genre="drama",
            target_duration=30.0,
        )
    report = director.get_production_report()
    assert report["title"] == "Report Test"
    assert report["scenes"] > 0
    assert report["total_shots"] > 0
    assert report["characters"] > 0


def test_director_get_production_report_before_production():
    """DirectorAgent should return a report even before production."""
    state = make_state()
    director = DirectorAgent(state)
    report = director.get_production_report()
    assert report["title"] == "N/A"
    assert report["scenes"] == 0


def test_director_log():
    """DirectorAgent log should add messages to state."""
    state = make_state()
    director = DirectorAgent(state)
    director.log("Test message")
    assert len(state.agent_messages) == 1
    assert state.agent_messages[0]["agent"] == "Director"
    assert state.agent_messages[0]["message"] == "Test message"


def test_director_merge_visual_prompts():
    """_merge_visual_prompts should combine shot and character prompts."""
    state = make_state()
    director = DirectorAgent(state)
    result = director._merge_visual_prompts("A shot description", "character look")
    assert "A shot description" in result
    assert "character look" in result
    assert "featuring" in result


def test_director_merge_visual_prompts_no_shot():
    """_merge_visual_prompts should handle missing shot prompt."""
    state = make_state()
    director = DirectorAgent(state)
    result = director._merge_visual_prompts(None, "character look")
    assert result == "character look"
