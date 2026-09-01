"""Sound Designer agent for soundtrack and foley generation."""


from director_gpt.agents import BaseAgent
from director_gpt.models import EmotionalTone, SoundCue, SoundtrackSegment
from director_gpt.models.project import ProjectState


class SoundDesignerAgent(BaseAgent):
    """Analyzes emotional cues to generate timed background scores and sound effects."""

    def get_role_description(self) -> str:
        return "Creates emotionally-matched soundtrack and precisely-timed foley effects"

    def __init__(self, name: str, state: ProjectState, llm_client=None):
        super().__init__(name, state, llm_client=llm_client)

    def process(self, input_data: dict) -> dict:
        """Generate soundtrack and sound cues from script."""
        mode = input_data.get("mode", "generate")
        script = input_data.get("script", {})
        scenes = script.get("scenes", [])

        self.log(f"Analyzing {len(scenes)} scenes for audio design")

        if mode == "critique":
            return self._critique_script(scenes)

        soundtrack = self._generate_soundtrack(scenes)
        self.log(f"Created {len(soundtrack)} soundtrack segments")

        sound_cues = self._generate_sound_cues(scenes)
        self.log(f"Created {len(sound_cues)} sound cues")

        return {
            "soundtrack": soundtrack,
            "sound_cues": sound_cues,
        }

    def _critique_script(self, scenes: list[dict]) -> dict:
        """Critique the script for emotional pacing issues."""
        critique_notes = []

        for scene in scenes:
            emotional_tone = scene.get("emotional_tone", "neutral")
            scene_duration = sum(shot.get("duration_seconds", 3.0) for shot in scene.get("shots", []))

            if scene_duration > 30 and emotional_tone in ["tense", "horror"]:
                critique_notes.append({
                    "type": "emotional_alignment",
                    "scene_number": scene.get("scene_number"),
                    "suggestion": f"Consider breaking up long {emotional_tone} scene to maintain tension",
                })

            if scene_duration < 5 and emotional_tone in ["romantic", "serene"]:
                critique_notes.append({
                    "type": "emotional_alignment",
                    "scene_number": scene.get("scene_number"),
                    "suggestion": f"Extend {emotional_tone} moment for emotional impact",
                })

        if not critique_notes:
            critique_notes.append({
                "type": "emotional_alignment",
                "scene_number": None,
                "suggestion": "Emotional pacing looks balanced",
            })

        return {
            "critique_notes": critique_notes,
        }

    def _generate_soundtrack(self, scenes: list[dict]) -> list[dict]:
        """Generate soundtrack segments matching scene emotions."""
        soundtrack = []
        current_time = 0.0

        for scene in scenes:
            scene_duration = sum(shot.get("duration_seconds", 3.0) for shot in scene.get("shots", []))
            emotional_tone = scene.get("emotional_tone", "neutral")

            segments = self._create_segments_for_scene(
                current_time, scene_duration, emotional_tone, scene
            )
            soundtrack.extend(segments)

            current_time += scene_duration

        return [s.to_dict() if hasattr(s, 'to_dict') else s for s in soundtrack]

    def _create_segments_for_scene(self, start_time: float, duration: float,
                                    emotional_tone: str, scene: dict) -> list[SoundtrackSegment]:
        """Create soundtrack segments for a scene."""
        tone = EmotionalTone(emotional_tone) if emotional_tone in [e.value for e in EmotionalTone] else EmotionalTone.NEUTRAL

        mood_config = self._get_mood_config(tone)

        segments = []

        intro_duration = min(3.0, duration * 0.15)
        segments.append(SoundtrackSegment(
            start_time=start_time,
            end_time=start_time + intro_duration,
            mood=tone,
            tempo=mood_config["tempo"],
            instruments=mood_config["instruments"],
            description=f"Intro: {mood_config['description']}",
        ))

        if duration > intro_duration:
            segments.append(SoundtrackSegment(
                start_time=start_time + intro_duration,
                end_time=start_time + duration,
                mood=tone,
                tempo=mood_config["tempo"],
                instruments=mood_config["instruments"],
                description=f"Main: {mood_config['description']}",
            ))

        return segments

    def _get_mood_config(self, tone: EmotionalTone) -> dict:
        """Get musical configuration for an emotional tone."""
        configs = {
            EmotionalTone.JOYFUL: {
                "tempo": "upbeat, 120-140 BPM",
                "instruments": ["acoustic guitar", "piano", "light percussion", "strings"],
                "description": "Bright, optimistic melody with gentle rhythm",
            },
            EmotionalTone.MELANCHOLIC: {
                "tempo": "slow, 60-70 BPM",
                "instruments": ["solo piano", "cello", "ambient pads"],
                "description": "Melancholic piano with sparse, emotional accompaniment",
            },
            EmotionalTone.TENSE: {
                "tempo": "building, 90-120 BPM",
                "instruments": ["low strings", "synthesizer", "percussion", "brass stabs"],
                "description": "Suspenseful build with dissonant undertones",
            },
            EmotionalTone.ROMANTIC: {
                "tempo": "moderate, 70-85 BPM",
                "instruments": ["strings", "piano", "harp", "woodwinds"],
                "description": "Warm, sweeping romantic theme",
            },
            EmotionalTone.HORROR: {
                "tempo": "irregular, unsettling",
                "instruments": ["dissonant strings", "prepared piano", "electronic drones", "found sounds"],
                "description": "Atonal, unsettling soundscape with sudden stings",
            },
            EmotionalTone.TRIUMPHANT: {
                "tempo": "march, 100-120 BPM",
                "instruments": ["full orchestra", "brass", "timpani", "choir"],
                "description": "Grand, heroic orchestral theme",
            },
            EmotionalTone.SERENE: {
                "tempo": "slow, 50-60 BPM",
                "instruments": ["ambient pads", "nature sounds", "soft piano", "flute"],
                "description": "Peaceful, meditative soundscape",
            },
            EmotionalTone.ANGRY: {
                "tempo": "fast, aggressive, 140-160 BPM",
                "instruments": ["distorted guitar", "heavy drums", "bass", "brass"],
                "description": "Aggressive, driving rhythm with power",
            },
            EmotionalTone.MYSTERIOUS: {
                "tempo": "moderate, 75-90 BPM",
                "instruments": ["muted strings", "clarinet", "vibraphone", "electronic textures"],
                "description": "Enigmatic, curious theme with unexpected turns",
            },
            EmotionalTone.NEUTRAL: {
                "tempo": "moderate, 80-100 BPM",
                "instruments": ["piano", "light strings", "ambient textures"],
                "description": "Understated, neutral background score",
            },
        }
        return configs.get(tone, configs[EmotionalTone.NEUTRAL])

    def _generate_sound_cues(self, scenes: list[dict]) -> list[dict]:
        """Generate specific sound effect cues."""
        cues = []
        current_time = 0.0

        for scene in scenes:
            scene_cues = self._analyze_scene_for_cues(scene, current_time)
            cues.extend(scene_cues)

            scene_duration = sum(shot.get("duration_seconds", 3.0) for shot in scene.get("shots", []))
            current_time += scene_duration

        return [c.to_dict() if hasattr(c, 'to_dict') else c for c in cues]

    def _analyze_scene_for_cues(self, scene: dict, time_offset: float) -> list[SoundCue]:
        """Analyze a scene for required sound effects."""
        cues = []
        location = scene.get("location", "").lower()

        ambient_cue = self._get_ambient_sound(location, time_offset, scene)
        if ambient_cue:
            cues.append(ambient_cue)

        for shot in scene.get("shots", []):
            shot_cues = self._get_shot_sound_cues(shot, time_offset, location)
            cues.extend(shot_cues)
            time_offset += shot.get("duration_seconds", 3.0)

        return cues

    def _get_ambient_sound(self, location: str, time_offset: float, scene: dict) -> SoundCue | None:
        """Get ambient sound for a location."""
        ambient_map = {
            "city": ("city ambience", "traffic, distant voices, urban hum"),
            "street": ("street ambience", "footsteps, traffic, city sounds"),
            "forest": ("forest ambience", "birds, wind in leaves, distant water"),
            "ocean": ("ocean ambience", "waves, seagulls, wind"),
            "room": ("room tone", "subtle air conditioning, faint outside noise"),
            "office": ("office ambience", "keyboard clicks, phones, HVAC"),
            "cafe": ("cafe ambience", "cups clinking, quiet conversation, espresso machine"),
            "garage": ("garage ambience", "echo, distant traffic, electrical hum"),
            "rooftop": ("rooftop ambience", "wind, distant city, pigeons"),
        }

        for key, (cue_type, description) in ambient_map.items():
            if key in location:
                scene_duration = sum(shot.get("duration_seconds", 3.0) for shot in scene.get("shots", []))
                return SoundCue(
                    timestamp=time_offset,
                    duration=scene_duration,
                    cue_type="ambient",
                    description=description,
                    intensity=0.3,
                )

        return None

    def _get_shot_sound_cues(self, shot: dict, time_offset: float, location: str) -> list[SoundCue]:
        """Get sound cues for a specific shot."""
        cues = []
        shot_type = shot.get("shot_type", "")
        description = shot.get("description", "").lower()

        if "door" in description:
            cues.append(SoundCue(
                timestamp=time_offset + 0.5,
                duration=1.0,
                cue_type="foley",
                description="Door handle turn and creak",
                intensity=0.6,
            ))

        if "phone" in description or "call" in description:
            cues.append(SoundCue(
                timestamp=time_offset,
                duration=2.0,
                cue_type="foley",
                description="Phone vibration and ring",
                intensity=0.5,
            ))

        if "rain" in location or "storm" in description:
            cues.append(SoundCue(
                timestamp=time_offset,
                duration=shot.get("duration_seconds", 3.0),
                cue_type="ambient",
                description="Rain on surfaces, thunder distant",
                intensity=0.4,
            ))

        if shot_type == "close_up" and shot.get("dialogue"):
            cues.append(SoundCue(
                timestamp=time_offset,
                duration=shot.get("duration_seconds", 3.0),
                cue_type="dialogue",
                description=f"Dialogue: {shot['dialogue'][:50]}...",
                intensity=0.8,
            ))

        return cues
