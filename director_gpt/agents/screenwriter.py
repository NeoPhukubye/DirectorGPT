"""Screenwriter agent for script generation and storyboarding."""

import math
from typing import Optional

from director_gpt.agents import BaseAgent, MessageType
from director_gpt.models import ShotType, EmotionalTone


class ScreenwriterAgent(BaseAgent):
    """Deconstructs prompts into scenes, character arcs, and shot-by-shot storyboards."""

    def get_role_description(self) -> str:
        return "Transforms high-level prompts into detailed screenplays with shot-by-shot storyboards"

    def process(self, input_data: dict) -> dict:
        """Generate screenplay from prompt."""
        prompt = input_data.get("prompt", "")
        target_duration = input_data.get("target_duration", 60.0)
        genre = input_data.get("genre", "drama")

        self.log(f"Writing screenplay for: '{prompt[:60]}...'")
        self.log(f"Target duration: {target_duration}s, Genre: {genre}")

        characters = self._create_characters(prompt, genre)
        self.log(f"Created {len(characters)} characters")

        scenes = self._create_scenes(prompt, genre, target_duration, characters)
        self.log(f"Created {len(scenes)} scenes with {sum(len(s['shots']) for s in scenes)} total shots")

        return {
            "characters": characters,
            "scenes": scenes,
            "genre": genre,
        }

    def _create_characters(self, prompt: str, genre: str) -> list[dict]:
        """Extract and create characters from the prompt."""
        characters = []

        protagonist = {
            "name": "Alex",
            "description": "A determined protagonist facing an impossible choice",
            "visual_prompt": "cinematic portrait, dramatic lighting, 35mm film grain",
            "voice_description": "measured, thoughtful voice with underlying tension",
        }
        characters.append(protagonist)

        if "mystery" in prompt.lower() or "detective" in prompt.lower():
            characters.append({
                "name": "The Stranger",
                "description": "A mysterious figure who appears at crucial moments",
                "visual_prompt": "shadowy silhouette, noir lighting, fedora hat, trench coat",
                "voice_description": "raspy whisper, deliberate pauses",
            })
        elif "love" in prompt.lower() or "romance" in genre.lower():
            characters.append({
                "name": "Jordan",
                "description": "The love interest, warm but guarded",
                "visual_prompt": "soft focus, natural light, genuine smile",
                "voice_description": "warm, melodic voice",
            })
        else:
            characters.append({
                "name": "Morgan",
                "description": "A pragmatic ally with hidden depths",
                "visual_prompt": "practical clothing, confident posture, sharp eyes",
                "voice_description": "direct, clipped speech",
            })

        return characters

    def _create_scenes(self, prompt: str, genre: str, target_duration: float,
                       characters: list[dict]) -> list[dict]:
        """Create scene breakdown with shots."""
        num_scenes = max(2, min(5, int(target_duration / 20)))
        scene_duration = target_duration / num_scenes

        scenes = []
        story_beats = self._get_story_beats(genre)

        for i in range(num_scenes):
            beat = story_beats[i % len(story_beats)]
            scene_num = i + 1

            shots = self._create_shots_for_scene(
                scene_num, beat, scene_duration, characters
            )

            scenes.append({
                "scene_number": scene_num,
                "title": f"Scene {scene_num}: {beat['title']}",
                "location": beat["location"],
                "time_of_day": beat["time_of_day"],
                "description": beat["description"],
                "emotional_tone": beat["emotional_tone"],
                "characters": beat.get("characters", [c["name"] for c in characters[:2]]),
                "environment_prompt": beat.get("environment_prompt"),
                "shots": shots,
            })

        return scenes

    def _create_shots_for_scene(self, scene_num: int, beat: dict,
                                 scene_duration: float,
                                 characters: list[dict]) -> list[dict]:
        """Create detailed shots for a scene."""
        num_shots = max(3, min(6, int(scene_duration / 5)))
        shot_duration = scene_duration / num_shots

        shots = []
        shot_types_sequence = self._get_shot_sequence(beat["emotional_tone"])

        for j in range(num_shots):
            shot_type = shot_types_sequence[j % len(shot_types_sequence)]
            shot_num = j + 1

            shot = {
                "shot_number": shot_num,
                "shot_type": shot_type.value,
                "description": self._generate_shot_description(shot_type, beat, j),
                "duration_seconds": round(shot_duration, 1),
                "camera_movement": self._get_camera_movement(shot_type, j),
                "visual_prompt": self._generate_visual_prompt(shot_type, beat, characters),
                "characters": beat.get("characters", [characters[0]["name"]]) if j < 2 else [],
                "emotional_tone": beat["emotional_tone"],
            }

            if j == len(shots) // 2 and "dialogue" in beat:
                shot["dialogue"] = beat["dialogue"]

            shots.append(shot)

        return shots

    def _get_story_beats(self, genre: str) -> list[dict]:
        """Get genre-appropriate story beats."""
        beats = {
            "drama": [
                {
                    "title": "The Ordinary World",
                    "location": "urban apartment, interior",
                    "time_of_day": "morning",
                    "description": "Protagonist begins their day, unaware of what's coming",
                    "emotional_tone": "neutral",
                    "environment_prompt": "soft morning light through windows, lived-in space, warm tones",
                },
                {
                    "title": "The Call",
                    "location": "city street, exterior",
                    "time_of_day": "afternoon",
                    "description": "An unexpected event disrupts the ordinary",
                    "emotional_tone": "tense",
                    "dialogue": "We need to talk. It's happening.",
                    "environment_prompt": "busy cityscape, harsh shadows, overcast sky",
                },
                {
                    "title": "Rising Action",
                    "location": "underground parking garage, interior",
                    "time_of_day": "night",
                    "description": "Tension builds as stakes become clear",
                    "emotional_tone": "mysterious",
                    "environment_prompt": "fluorescent lights, concrete pillars, deep shadows, green tint",
                },
                {
                    "title": "The Confrontation",
                    "location": "rooftop, exterior",
                    "time_of_day": "dusk",
                    "description": "Everything comes to a head",
                    "emotional_tone": "tense",
                    "dialogue": "There's no going back from this.",
                    "environment_prompt": "golden hour light, city skyline, wind, dramatic clouds",
                },
                {
                    "title": "Resolution",
                    "location": "quiet cafe, interior",
                    "time_of_day": "dawn",
                    "description": "Aftermath and new understanding",
                    "emotional_tone": "serene",
                    "environment_prompt": "warm candlelight, rain on windows, intimate atmosphere",
                },
            ],
            "horror": [
                {
                    "title": "Unease",
                    "location": "suburban house, interior",
                    "time_of_day": "night",
                    "description": "Something feels wrong",
                    "emotional_tone": "mysterious",
                    "environment_prompt": "dark rooms, flickering lights, long shadows, blue moonlight",
                },
                {
                    "title": "Discovery",
                    "location": "basement, interior",
                    "time_of_day": "night",
                    "description": "The source of dread revealed",
                    "emotional_tone": "horror",
                    "environment_prompt": "single bulb, stone walls, water dripping, darkness pressing in",
                },
                {
                    "title": "Escape",
                    "location": "forest, exterior",
                    "time_of_day": "night",
                    "description": "Running from the terror",
                    "emotional_tone": "tense",
                    "environment_prompt": "dense fog, bare trees, moonlight breaking through",
                },
                {
                    "title": "Confrontation",
                    "location": "abandoned building, interior",
                    "time_of_day": "night",
                    "description": "Face to face with the horror",
                    "emotional_tone": "horror",
                    "environment_prompt": "decay, peeling wallpaper, complete darkness with flashlight",
                },
            ],
            "comedy": [
                {
                    "title": "Setup",
                    "location": "office, interior",
                    "time_of_day": "morning",
                    "description": "Everything seems normal",
                    "emotional_tone": "neutral",
                    "environment_prompt": "bright fluorescent lights, cubicles, coffee cups",
                },
                {
                    "title": "Complication",
                    "location": "elevator, interior",
                    "time_of_day": "midday",
                    "description": "Things start going wrong",
                    "emotional_tone": "joyful",
                    "dialogue": "This is fine. Everything is fine.",
                    "environment_prompt": "cramped space, harsh lighting, awkward angles",
                },
                {
                    "title": "Chaos",
                    "location": "restaurant, interior",
                    "time_of_day": "evening",
                    "description": "Everything falls apart",
                    "emotional_tone": "joyful",
                    "environment_prompt": "romantic lighting gone wrong, overturned tables, dramatic",
                },
            ],
        }

        return beats.get(genre.lower(), beats["drama"])

    def _get_shot_sequence(self, emotional_tone: str) -> list[ShotType]:
        """Get appropriate shot sequence for emotional tone."""
        sequences = {
            "tense": [ShotType.WIDE, ShotType.MEDIUM, ShotType.CLOSE_UP, ShotType.CLOSE_UP],
            "mysterious": [ShotType.WIDE, ShotType.WIDE, ShotType.MEDIUM, ShotType.INSERT],
            "joyful": [ShotType.WIDE, ShotType.MEDIUM, ShotType.MEDIUM, ShotType.CLOSE_UP],
            "horror": [ShotType.WIDE, ShotType.MEDIUM, ShotType.EXTREME_CLOSE_UP, ShotType.POV],
            "serene": [ShotType.AERIAL, ShotType.WIDE, ShotType.WIDE, ShotType.MEDIUM],
            "romantic": [ShotType.MEDIUM, ShotType.CLOSE_UP, ShotType.OVER_SHOULDER, ShotType.CLOSE_UP],
            "neutral": [ShotType.WIDE, ShotType.MEDIUM, ShotType.MEDIUM, ShotType.CLOSE_UP],
        }
        return sequences.get(emotional_tone, sequences["neutral"])

    def _generate_shot_description(self, shot_type: ShotType, beat: dict, shot_index: int) -> str:
        """Generate description for a shot."""
        descriptions = {
            ShotType.WIDE: f"Establishing shot of {beat['location']}",
            ShotType.MEDIUM: "Medium shot capturing character interaction",
            ShotType.CLOSE_UP: "Intimate close-up revealing emotion",
            ShotType.EXTREME_CLOSE_UP: "Extreme detail shot for emphasis",
            ShotType.OVER_SHOULDER: "Over-the-shoulder perspective",
            ShotType.POV: "Point-of-view shot from character perspective",
            ShotType.INSERT: "Detail insert of important object",
            ShotType.AERIAL: "Bird's eye view establishing geography",
        }
        return descriptions.get(shot_type, "Standard shot")

    def _get_camera_movement(self, shot_type: ShotType, shot_index: int) -> Optional[str]:
        """Determine camera movement for shot."""
        movements = {
            ShotType.WIDE: "slow pan left to right",
            ShotType.MEDIUM: "subtle push in",
            ShotType.CLOSE_UP: "static, locked off",
            ShotType.EXTREME_CLOSE_UP: "rack focus",
            ShotType.OVER_SHOULDER: "gentle float",
            ShotType.POV: "handheld, natural movement",
            ShotType.INSERT: "static macro",
            ShotType.AERIAL: "crane down to establish",
        }
        if shot_index % 2 == 0:
            return movements.get(shot_type)
        return "static"

    def _generate_visual_prompt(self, shot_type: ShotType, beat: dict,
                                 characters: list[dict]) -> str:
        """Generate visual prompt for image generation."""
        base_prompt = beat.get("environment_prompt", "cinematic scene")
        shot_descriptors = {
            ShotType.WIDE: "wide establishing shot",
            ShotType.MEDIUM: "medium shot, rule of thirds",
            ShotType.CLOSE_UP: "close-up portrait, shallow depth of field",
            ShotType.EXTREME_CLOSE_UP: "extreme detail, macro lens",
            ShotType.OVER_SHOULDER: "over-shoulder framing, bokeh background",
            ShotType.POV: "first-person perspective, immersive",
            ShotType.INSERT: "insert shot, sharp focus",
            ShotType.AERIAL: "aerial drone shot, sweeping view",
        }

        prompt = f"{shot_descriptors.get(shot_type, '')}, {base_prompt}"
        if characters and shot_type in [ShotType.MEDIUM, ShotType.CLOSE_UP]:
            prompt += f", {characters[0].get('visual_prompt', '')}"

        return f"{prompt}, cinematic lighting, film grain, 35mm, professional color grading"
