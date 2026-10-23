"""Tests for data models."""

from director_gpt.models import (
    Character,
    EditDecision,
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


def test_shot_from_dict_defaults():
    shot = Shot.from_dict(
        {
            "shot_number": 2,
            "shot_type": "wide",
            "description": "Test",
            "duration_seconds": 7.5,
            "emotional_tone": "tense",
        }
    )
    assert shot.shot_number == 2
    assert shot.shot_type == ShotType.WIDE
    assert shot.duration_seconds == 7.5
    assert shot.emotional_tone == EmotionalTone.TENSE


def test_shot_from_dict_invalid_enum_defaults():
    shot = Shot.from_dict({"shot_type": "not_a_real_type", "emotional_tone": "bogus"})
    assert shot.shot_type == ShotType.MEDIUM
    assert shot.emotional_tone == EmotionalTone.NEUTRAL


def test_shot_roundtrip():
    original = Shot(
        shot_number=1,
        shot_type=ShotType.CLOSE_UP,
        description="Round trip",
        duration_seconds=4.0,
        emotional_tone=EmotionalTone.JOYFUL,
    )
    restored = Shot.from_dict(original.to_dict())
    assert restored == original


def test_scene_from_dict_with_shots():
    data = {
        "scene_number": 1,
        "title": "Test",
        "location": "loc",
        "time_of_day": "day",
        "description": "desc",
        "emotional_tone": "neutral",
        "shots": [
            {
                "shot_number": 1,
                "shot_type": "medium",
                "description": "s1",
                "duration_seconds": 3.0,
            }
        ],
    }
    scene = Scene.from_dict(data)
    assert scene.scene_number == 1
    assert len(scene.shots) == 1
    assert scene.shots[0].shot_type == ShotType.MEDIUM


def test_film_script_from_dict():
    data = {
        "title": "Loaded Film",
        "logline": "From dict",
        "genre": "comedy",
        "total_duration_estimate": 30.0,
        "characters": [{"name": "Sam", "description": "Protagonist", "visual_prompt": "heroic"}],
        "scenes": [
            {
                "scene_number": 1,
                "title": "S1",
                "location": "office",
                "time_of_day": "morning",
                "description": "Opening",
                "emotional_tone": "joyful",
                "shots": [],
            }
        ],
    }
    script = FilmScript.from_dict(data)
    assert script.title == "Loaded Film"
    assert script.genre == "comedy"
    assert len(script.characters) == 1
    assert script.characters[0].name == "Sam"
    assert len(script.scenes) == 1
    assert script.scenes[0].emotional_tone == EmotionalTone.JOYFUL


def test_edit_decision_from_dict():
    data = {
        "shot_index": 3,
        "transition_in": "fade_in",
        "transition_out": "dissolve",
        "transition_duration": 0.7,
        "speed_adjustment": 1.1,
        "color_grade": "warm",
    }
    decision = EditDecision.from_dict(data)
    assert decision.shot_index == 3
    assert decision.transition_in == TransitionType.FADE_IN
    assert decision.transition_out == TransitionType.DISSOLVE
    assert decision.speed_adjustment == 1.1
    assert decision.color_grade == "warm"
