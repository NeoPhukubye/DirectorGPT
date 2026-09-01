"""Data models for film production pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import timedelta


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


@dataclass
class Character:
    name: str
    description: str
    visual_prompt: str
    voice_description: Optional[str] = None
    consistency_embedding: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "visual_prompt": self.visual_prompt,
            "voice_description": self.voice_description,
            "consistency_embedding": self.consistency_embedding,
        }


@dataclass
class Shot:
    shot_number: int
    shot_type: ShotType
    description: str
    duration_seconds: float
    dialogue: Optional[str] = None
    action: Optional[str] = None
    camera_movement: Optional[str] = None
    visual_prompt: Optional[str] = None
    characters: list[str] = field(default_factory=list)
    emotional_tone: EmotionalTone = EmotionalTone.NEUTRAL
    generated_image_path: Optional[str] = None
    generated_video_path: Optional[str] = None

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
    environment_prompt: Optional[str] = None

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


@dataclass
class SoundCue:
    timestamp: float
    duration: float
    cue_type: str
    description: str
    intensity: float = 0.5
    generated_audio_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "duration": self.duration,
            "cue_type": self.cue_type,
            "description": self.description,
            "intensity": self.intensity,
            "generated_audio_path": self.generated_audio_path,
        }


@dataclass
class SoundtrackSegment:
    start_time: float
    end_time: float
    mood: EmotionalTone
    tempo: str
    instruments: list[str]
    description: str
    generated_audio_path: Optional[str] = None

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


@dataclass
class EditDecision:
    shot_index: int
    transition_in: TransitionType
    transition_out: TransitionType
    transition_duration: float = 0.5
    speed_adjustment: float = 1.0
    color_grade: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "shot_index": self.shot_index,
            "transition_in": self.transition_in.value,
            "transition_out": self.transition_out.value,
            "transition_duration": self.transition_duration,
            "speed_adjustment": self.speed_adjustment,
            "color_grade": self.color_grade,
        }


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
            "sound_cues": [s.to_dict() for s in self.sound_cues],
            "edit_decisions": [e.to_dict() for e in self.edit_decisions],
        }
