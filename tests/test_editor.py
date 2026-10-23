"""Tests for the EditorAgent."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from director_gpt.agents.editor import EditorAgent, VideoRenderer
from director_gpt.models import (
    EmotionalTone,
    FilmScript,
    Scene,
    Shot,
    ShotType,
    TransitionType,
)
from director_gpt.models.project import ProjectConfig, ProjectState


def make_state() -> ProjectState:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ProjectConfig(
            project_name="test",
            output_dir=Path(tmpdir) / "output",
        )
        return ProjectState(config=config)


def make_test_script() -> FilmScript:
    shots = [
        Shot(
            shot_number=1,
            shot_type=ShotType.WIDE,
            description="Opening shot",
            duration_seconds=5.0,
            emotional_tone=EmotionalTone.NEUTRAL,
        ),
        Shot(
            shot_number=2,
            shot_type=ShotType.MEDIUM,
            description="Close up",
            duration_seconds=3.0,
            emotional_tone=EmotionalTone.TENSE,
        ),
    ]
    scene = Scene(
        scene_number=1,
        title="Test Scene",
        location="test location",
        time_of_day="day",
        description="A test scene",
        emotional_tone=EmotionalTone.NEUTRAL,
        shots=shots,
    )
    return FilmScript(
        title="Test Film",
        logline="A test",
        genre="drama",
        total_duration_estimate=10.0,
        scenes=[scene],
    )


def test_editor_initialization():
    """EditorAgent should initialize properly."""
    state = make_state()
    agent = EditorAgent("Editor", state)
    assert agent.name == "Editor"
    assert agent.state is state


def test_editor_process():
    """EditorAgent process should generate edit decisions."""
    state = make_state()
    agent = EditorAgent("Editor", state)
    script = make_test_script()
    result = agent.process(
        {
            "script": script.to_dict(),
            "config": {"fps": 24, "resolution": (1920, 1080), "output_dir": "/tmp"},
        }
    )
    assert "edit_decisions" in result
    assert len(result["edit_decisions"]) == 2
    assert result["edit_decisions"][0]["shot_index"] == 0
    assert result["edit_decisions"][1]["shot_index"] == 1


def test_editor_determine_transitions_first_shot():
    """First shot should have fade_in transition."""
    state = make_state()
    agent = EditorAgent("Editor", state)
    trans_in, trans_out = agent._determine_transitions(0, 3, "neutral")
    assert trans_in == TransitionType.FADE_IN


def test_editor_determine_transitions_last_shot():
    """Last shot should have fade_out transition."""
    state = make_state()
    agent = EditorAgent("Editor", state)
    trans_in, trans_out = agent._determine_transitions(2, 3, "neutral")
    assert trans_out == TransitionType.FADE_OUT


def test_editor_determine_transitions_tense():
    """Tense scenes should use cut transitions."""
    state = make_state()
    agent = EditorAgent("Editor", state)
    trans_in, trans_out = agent._determine_transitions(1, 3, "tense")
    assert trans_in == TransitionType.CUT


def test_editor_determine_transitions_romantic():
    """Romantic scenes should use dissolve transitions."""
    state = make_state()
    agent = EditorAgent("Editor", state)
    trans_in, trans_out = agent._determine_transitions(1, 3, "romantic")
    assert trans_in == TransitionType.DISSOLVE


def test_editor_get_speed_adjustment():
    """Speed adjustment should vary by emotional tone."""
    state = make_state()
    agent = EditorAgent("Editor", state)
    assert agent._get_speed_adjustment("tense") == 1.0
    assert agent._get_speed_adjustment("horror") == 0.9
    assert agent._get_speed_adjustment("serene") == 0.85
    assert agent._get_speed_adjustment("unknown") == 1.0


def test_editor_get_color_grade():
    """Color grade should vary by emotional tone."""
    state = make_state()
    agent = EditorAgent("Editor", state)
    assert agent._get_color_grade("tense") is not None
    assert agent._get_color_grade("horror") is not None
    assert agent._get_color_grade("neutral") is None


def test_video_renderer_initialization(tmp_path):
    """VideoRenderer should create output directory."""
    output_dir = tmp_path / "rendered"
    renderer = VideoRenderer(str(output_dir))
    assert renderer.output_dir.exists()
    assert renderer.output_dir == output_dir


def test_video_renderer_stitch_no_shots():
    """VideoRenderer should raise ValueError when no shots exist."""
    renderer = VideoRenderer("/tmp/test_render")
    empty_script = {"scenes": [], "edit_decisions": [], "soundtrack": []}
    try:
        renderer.stitch_production(empty_script, "test")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "No shots" in str(e)


def test_video_renderer_stitch_with_images(tmp_path):
    """VideoRenderer should stitch images into video using FFmpeg."""
    output_dir = tmp_path / "rendered"
    renderer = VideoRenderer(str(output_dir))

    # Create a test image
    img_path = tmp_path / "test_image.png"
    img_path.write_bytes(b"fake image data")

    script_data = {
        "scenes": [
            {
                "shots": [
                    {
                        "shot_number": 1,
                        "description": "Test shot",
                        "duration_seconds": 1.0,
                        "generated_image_path": str(img_path),
                    }
                ]
            }
        ],
        "edit_decisions": [],
        "soundtrack": [],
    }

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        # Mock Path methods to avoid actual file operations
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.rename"):
                with patch("pathlib.Path.unlink"):
                    with patch("builtins.open", MagicMock()):
                        result = renderer.stitch_production(script_data, "test_film")
                        assert mock_run.called
                        assert "test_film_final_cut" in result
