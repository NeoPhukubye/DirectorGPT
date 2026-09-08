"""Tests for data models."""

from director_gpt.models import (
    Character,
    EmotionalTone,
    FilmScript,
    Scene,
    Shot,
    ShotType,
    SoundCue,
    SoundtrackSegment,
    TransitionType,
)


def test_shot_type_values():
    assert ShotType.WIDE.value == "wide"
    assert ShotType.MEDIUM.value == "medium"
    assert ShotType.CLOSE_UP.value == "close_up"


def test_transition_type_values():
    assert TransitionType.CUT.value == "cut"
    assert TransitionType.FADE_IN.value == "fade_in"


def test_emotional_tone_values():
    assert EmotionalTone.JOYFUL.value == "joyful"
    assert EmotionalTone.HORROR.value == "horror"
    assert EmotionalTone.NEUTRAL.value == "neutral"


def test_shot_to_dict():
    shot = Shot(
        shot_number=1,
        shot_type=ShotType.WIDE,
        description="Test shot",
        duration_seconds=5.0,
        emotional_tone=EmotionalTone.NEUTRAL,
    )
    d = shot.to_dict()
    assert d["shot_number"] == 1
    assert d["shot_type"] == "wide"
    assert d["duration_seconds"] == 5.0
    assert d["emotional_tone"] == "neutral"


def test_scene_total_duration():
    shots = [
        Shot(1, ShotType.WIDE, "Shot 1", 3.0),
        Shot(2, ShotType.MEDIUM, "Shot 2", 7.0),
    ]
    scene = Scene(
        scene_number=1,
        title="Test",
        location="test",
        time_of_day="day",
        description="Test scene",
        emotional_tone=EmotionalTone.NEUTRAL,
        shots=shots,
    )
    assert scene.total_duration == 10.0


def test_film_script_total_duration():
    shots1 = [Shot(1, ShotType.WIDE, "S1", 5.0)]
    shots2 = [Shot(1, ShotType.MEDIUM, "S2", 3.0)]
    scenes = [
        Scene(1, "Scene 1", "loc", "day", "desc", EmotionalTone.NEUTRAL, shots1),
        Scene(2, "Scene 2", "loc", "night", "desc", EmotionalTone.NEUTRAL, shots2),
    ]
    script = FilmScript(
        title="Test",
        logline="Test logline",
        genre="drama",
        total_duration_estimate=10.0,
        scenes=scenes,
    )
    assert script.total_duration == 8.0


def test_character_to_dict():
    char = Character(
        name="Alex",
        description="A protagonist",
        visual_prompt="cinematic portrait",
    )
    d = char.to_dict()
    assert d["name"] == "Alex"
    assert d["description"] == "A protagonist"
    assert d["visual_prompt"] == "cinematic portrait"
    assert d["voice_description"] is None
    assert d["consistency_embedding"] is None


def test_sound_cue_to_dict():
    cue = SoundCue(
        timestamp=10.0,
        duration=2.0,
        cue_type="foley",
        description="Door creak",
        intensity=0.7,
    )
    d = cue.to_dict()
    assert d["timestamp"] == 10.0
    assert d["cue_type"] == "foley"
    assert d["intensity"] == 0.7


def test_soundtrack_segment_to_dict():
    seg = SoundtrackSegment(
        start_time=0.0,
        end_time=10.0,
        mood=EmotionalTone.TENSE,
        tempo="90 BPM",
        instruments=["strings", "synth"],
        description="Tension building",
    )
    d = seg.to_dict()
    assert d["start_time"] == 0.0
    assert d["mood"] == "tense"
    assert d["instruments"] == ["strings", "synth"]


def test_film_script_to_dict():
    script = FilmScript(
        title="Test Film",
        logline="A test",
        genre="drama",
        total_duration_estimate=60.0,
    )
    d = script.to_dict()
    assert d["title"] == "Test Film"
    assert d["logline"] == "A test"
    assert d["genre"] == "drama"
    assert d["characters"] == []
    assert d["scenes"] == []
