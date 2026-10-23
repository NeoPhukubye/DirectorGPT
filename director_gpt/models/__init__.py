"""Data models for film production pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar, cast

T = TypeVar("T", bound=Enum)


class ShotType(Enum):
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    OVER_SHOULDER = "over_shoulder"
    POV = "pov"
    INSERT = "insert"
    AERIAL = "aerial"


class TransitionType(Enum):
    CUT = "cut"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    JUMP_CUT = "jump_cut"
    MATCH_CUT = "match_cut"


class EmotionalTone(Enum):
    JOYFUL = "joyful"
    MELANCHOLIC = "melancholic"
    TENSE = "tense"
    ROMANTIC = "romantic"
    HORROR = "horror"
    TRIUMPHANT = "triumphant"
    SERENE = "serene"
    ANGRY = "angry"
    MYSTERIOUS = "mysterious"
    NEUTRAL = "neutral"


def parse_enum(value: Any, enum_cls: type[T], default: T | None = None) -> T:
    """Parse a value into an enum member, returning ``default`` on failure."""
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str) and value in [e.value for e in enum_cls]:
        return enum_cls(value)
    if default is not None:
        return default
    raise ValueError(f"Invalid {enum_cls.__name__} value: {value!r}")


def parse_shot_type(value: Any, default: ShotType = ShotType.MEDIUM) -> ShotType:
    """Parse a value into a :class:`ShotType` member."""
    return cast(ShotType, parse_enum(value, ShotType, default))


def parse_emotional_tone(
    value: Any, default: EmotionalTone = EmotionalTone.NEUTRAL
) -> EmotionalTone:
    """Parse a value into a :class:`EmotionalTone` member."""
    return cast(EmotionalTone, parse_enum(value, EmotionalTone, default))


def parse_transition_type(
    value: Any, default: TransitionType = TransitionType.CUT
) -> TransitionType:
    """Parse a value into a :class:`TransitionType` member."""
    return cast(TransitionType, parse_enum(value, TransitionType, default))


@dataclass
class Character:
    name: str
    description: str
    visual_prompt: str
    voice_description: str | None = None
    consistency_embedding: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "visual_prompt": self.visual_prompt,
            "voice_description": self.voice_description,
            "consistency_embedding": self.consistency_embedding,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        return cls(
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            visual_prompt=data.get("visual_prompt", ""),
            voice_description=data.get("voice_description"),
            consistency_embedding=data.get("consistency_embedding"),
        )


@dataclass
class Shot:
    shot_number: int
    shot_type: ShotType
    description: str
    duration_seconds: float
    dialogue: str | None = None
    action: str | None = None
    camera_movement: str | None = None
    visual_prompt: str | None = None
    characters: list[str] = field(default_factory=list)
    emotional_tone: EmotionalTone = EmotionalTone.NEUTRAL
    generated_image_path: str | None = None
    generated_video_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "shot_number": self.shot_number,
            "shot_type": self.shot_type.value,
            "description": self.description,
            "duration_seconds": self.duration_seconds,
            "dialogue": self.dialogue,
            "action": self.action,
            "camera_movement": self.camera_movement,
            "visual_prompt": self.visual_prompt,
            "characters": self.characters,
            "emotional_tone": self.emotional_tone.value,
            "generated_image_path": self.generated_image_path,
            "generated_video_path": self.generated_video_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Shot":
        return cls(
            shot_number=data.get("shot_number", 1),
            shot_type=parse_shot_type(data.get("shot_type")),
            description=data.get("description", ""),
            duration_seconds=float(data.get("duration_seconds", 3.0)),
            dialogue=data.get("dialogue"),
            action=data.get("action"),
            camera_movement=data.get("camera_movement"),
            visual_prompt=data.get("visual_prompt"),
            characters=list(data.get("characters", [])),
            emotional_tone=parse_emotional_tone(data.get("emotional_tone")),
            generated_image_path=data.get("generated_image_path"),
            generated_video_path=data.get("generated_video_path"),
        )


@dataclass
class Scene:
    scene_number: int
    title: str
    location: str
    time_of_day: str
    description: str
    emotional_tone: EmotionalTone
    shots: list[Shot] = field(default_factory=list)
    characters: list[str] = field(default_factory=list)
    environment_prompt: str | None = None

    @property
    def total_duration(self) -> float:
        return sum(shot.duration_seconds for shot in self.shots)

    def to_dict(self) -> dict:
        return {
            "scene_number": self.scene_number,
            "title": self.title,
            "location": self.location,
            "time_of_day": self.time_of_day,
            "description": self.description,
            "emotional_tone": self.emotional_tone.value,
            "shots": [s.to_dict() for s in self.shots],
            "characters": self.characters,
            "environment_prompt": self.environment_prompt,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        return cls(
            scene_number=data.get("scene_number", 1),
            title=data.get("title", ""),
            location=data.get("location", ""),
            time_of_day=data.get("time_of_day", ""),
            description=data.get("description", ""),
            emotional_tone=parse_emotional_tone(data.get("emotional_tone")),
            shots=[Shot.from_dict(s) for s in data.get("shots", [])],
            characters=list(data.get("characters", [])),
            environment_prompt=data.get("environment_prompt"),
        )


@dataclass
class SoundCue:
    timestamp: float
    duration: float
    cue_type: str
    description: str
    intensity: float = 0.5
    generated_audio_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "duration": self.duration,
            "cue_type": self.cue_type,
            "description": self.description,
            "intensity": self.intensity,
            "generated_audio_path": self.generated_audio_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SoundCue":
        return cls(
            timestamp=float(data.get("timestamp", 0.0)),
            duration=float(data.get("duration", 0.0)),
            cue_type=data.get("cue_type", "ambient"),
            description=data.get("description", ""),
            intensity=float(data.get("intensity", 0.5)),
            generated_audio_path=data.get("generated_audio_path"),
        )


@dataclass
class SoundtrackSegment:
    start_time: float
    end_time: float
    mood: EmotionalTone
    tempo: str
    instruments: list[str]
    description: str
    generated_audio_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "mood": self.mood.value,
            "tempo": self.tempo,
            "instruments": self.instruments,
            "description": self.description,
            "generated_audio_path": self.generated_audio_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SoundtrackSegment":
        return cls(
            start_time=float(data.get("start_time", 0.0)),
            end_time=float(data.get("end_time", 0.0)),
            mood=parse_emotional_tone(data.get("mood")),
            tempo=data.get("tempo", ""),
            instruments=list(data.get("instruments", [])),
            description=data.get("description", ""),
            generated_audio_path=data.get("generated_audio_path"),
        )


@dataclass
class EditDecision:
    shot_index: int
    transition_in: TransitionType
    transition_out: TransitionType
    transition_duration: float = 0.5
    speed_adjustment: float = 1.0
    color_grade: str | None = None

    def to_dict(self) -> dict:
        return {
            "shot_index": self.shot_index,
            "transition_in": self.transition_in.value,
            "transition_out": self.transition_out.value,
            "transition_duration": self.transition_duration,
            "speed_adjustment": self.speed_adjustment,
            "color_grade": self.color_grade,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EditDecision":
        return cls(
            shot_index=data.get("shot_index", 0),
            transition_in=parse_transition_type(data.get("transition_in")),
            transition_out=parse_transition_type(data.get("transition_out")),
            transition_duration=float(data.get("transition_duration", 0.5)),
            speed_adjustment=float(data.get("speed_adjustment", 1.0)),
            color_grade=data.get("color_grade"),
        )


@dataclass
class FilmScript:
    title: str
    logline: str
    genre: str
    total_duration_estimate: float
    characters: list[Character] = field(default_factory=list)
    scenes: list[Scene] = field(default_factory=list)
    soundtrack: list[SoundtrackSegment] = field(default_factory=list)
    sound_cues: list[SoundCue] = field(default_factory=list)
    edit_decisions: list[EditDecision] = field(default_factory=list)

    @property
    def total_duration(self) -> float:
        return sum(scene.total_duration for scene in self.scenes)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "logline": self.logline,
            "genre": self.genre,
            "total_duration_estimate": self.total_duration_estimate,
            "characters": [c.to_dict() for c in self.characters],
            "scenes": [s.to_dict() for s in self.scenes],
            "soundtrack": [s.to_dict() for s in self.soundtrack],
            "sound_cues": [c.to_dict() for c in self.sound_cues],
            "edit_decisions": [e.to_dict() for e in self.edit_decisions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FilmScript":
        return cls(
            title=data.get("title", "Untitled"),
            logline=data.get("logline", ""),
            genre=data.get("genre", "drama"),
            total_duration_estimate=float(data.get("total_duration_estimate", 60.0)),
            characters=[Character.from_dict(c) for c in data.get("characters", [])],
            scenes=[Scene.from_dict(s) for s in data.get("scenes", [])],
            soundtrack=[SoundtrackSegment.from_dict(s) for s in data.get("soundtrack", [])],
            sound_cues=[SoundCue.from_dict(c) for c in data.get("sound_cues", [])],
            edit_decisions=[EditDecision.from_dict(e) for e in data.get("edit_decisions", [])],
        )
