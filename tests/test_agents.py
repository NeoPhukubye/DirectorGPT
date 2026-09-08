"""Tests for agents."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from director_gpt.agents.casting import CastingAgent
from director_gpt.agents.screenwriter import ScreenwriterAgent
from director_gpt.agents.sound import SoundDesignerAgent
from director_gpt.models.project import ProjectConfig, ProjectState


def make_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ProjectConfig(
            project_name="test",
            output_dir=Path(tmpdir) / "output",
        )
        return ProjectState(config=config)


def test_screenwriter_rule_based():
    state = make_state()
    agent = ScreenwriterAgent("Screenwriter", state)
    result = agent.process(
        {
            "prompt": "A detective investigates a mystery",
            "target_duration": 60.0,
            "genre": "drama",
        }
    )
    assert "characters" in result
    assert "scenes" in result
    assert len(result["characters"]) >= 1
    assert len(result["scenes"]) >= 1
    total_shots = sum(len(s["shots"]) for s in result["scenes"])
    assert total_shots >= 3


def test_screenwriter_with_llm():
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
    agent = ScreenwriterAgent("Screenwriter", state, llm_client=mock_llm)
    result = agent.process(
        {
            "prompt": "A hero saves the day",
            "target_duration": 30.0,
            "genre": "action",
        }
    )
    assert len(result["characters"]) == 1
    assert result["characters"][0]["name"] == "Hero"
    assert len(result["scenes"]) == 1
    assert len(result["scenes"][0]["shots"]) == 1


def test_screenwriter_llm_fallback():
    state = make_state()
    mock_llm = MagicMock()
    mock_llm.generate.side_effect = Exception("API error")
    agent = ScreenwriterAgent("Screenwriter", state, llm_client=mock_llm)
    result = agent.process(
        {
            "prompt": "A detective investigates",
            "target_duration": 60.0,
            "genre": "drama",
        }
    )
    assert "characters" in result
    assert "scenes" in result


def test_casting_agent_critique():
    state = make_state()
    agent = CastingAgent("Casting", state)
    script = {
        "characters": [{"name": "Alex", "description": "Protagonist"}],
        "scenes": [
            {"scene_number": 1, "characters": ["Alex"]},
            {"scene_number": 2, "characters": ["Alex"]},
        ],
    }
    result = agent.process({"script": script, "mode": "critique"})
    assert "critique_notes" in result
    assert len(result["critique_notes"]) >= 1


def test_casting_agent_consistency():
    state = make_state()
    agent = CastingAgent("Casting", state)
    script = {
        "characters": [
            {"name": "Alex", "description": "A tall man with scar", "visual_prompt": "cinematic"}
        ],
        "scenes": [
            {"scene_number": 1, "location": "office", "environment_prompt": "modern office"},
        ],
    }
    result = agent.process({"script": script, "mode": "consistency"})
    assert "character_prompts" in result
    assert "environment_prompts" in result
    assert "Alex" in result["character_prompts"]
    assert "scar" in result["character_prompts"]["Alex"].lower()


def test_sound_agent_critique():
    state = make_state()
    agent = SoundDesignerAgent("Sound", state)
    script = {
        "scenes": [
            {
                "scene_number": 1,
                "emotional_tone": "tense",
                "shots": [
                    {"duration_seconds": 20.0},
                    {"duration_seconds": 20.0},
                ],
            }
        ]
    }
    result = agent.process({"script": script, "mode": "critique"})
    assert "critique_notes" in result


def test_sound_agent_generate():
    state = make_state()
    agent = SoundDesignerAgent("Sound", state)
    script = {
        "scenes": [
            {
                "scene_number": 1,
                "emotional_tone": "tense",
                "shots": [
                    {"duration_seconds": 5.0},
                    {"duration_seconds": 5.0},
                ],
            }
        ]
    }
    result = agent.process({"script": script, "mode": "generate"})
    assert "soundtrack" in result
    assert "sound_cues" in result
    assert len(result["soundtrack"]) >= 1
