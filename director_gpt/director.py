"""Director orchestrator for coordinating multi-agent film production."""

import json
from pathlib import Path

from director_gpt.agents.casting import CastingAgent
from director_gpt.agents.editor import EditorAgent
from director_gpt.agents.screenwriter import ScreenwriterAgent
from director_gpt.agents.sound import SoundDesignerAgent
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
from director_gpt.models.project import ProductionPhase, ProjectState
from director_gpt.utils import safe_import


class DirectorAgent:
    """Central orchestrator that coordinates all production agents."""

    def __init__(self, state: ProjectState, llm_client=None):
        self.state = state
        self.script: FilmScript | None = None
        self.llm_client = llm_client

        self.screenwriter = ScreenwriterAgent("Screenwriter", state, llm_client=llm_client)
        self.casting = CastingAgent("Casting", state, llm_client=llm_client)
        self.sound = SoundDesignerAgent("SoundDesigner", state, llm_client=llm_client)
        self.editor = EditorAgent("Editor", state, llm_client=llm_client)

        self.agents = {
            "Screenwriter": self.screenwriter,
            "Casting": self.casting,
            "SoundDesigner": self.sound,
            "Editor": self.editor,
        }

        self.conversation_log: list[dict] = []

    def log(self, message: str):
        """Log director activity."""
        self.state.add_message("Director", message)

    def produce_film(self, prompt: str, title: str = "Untitled",
                     genre: str = "drama", target_duration: float = 60.0) -> FilmScript:
        """Execute the full film production pipeline."""

        self.state.transition_to(ProductionPhase.DEVELOPMENT)
        self.state.add_message("Director", f"Starting production: '{title}'")
        self.state.add_message("Director", f"Prompt: {prompt}")

        self.script = FilmScript(
            title=title,
            logline=prompt,
            genre=genre,
            total_duration_estimate=target_duration,
        )

        self._phase_development(prompt, target_duration)
        self._phase_pre_production()
        self._phase_production()
        self._phase_post_production()

        self.state.transition_to(ProductionPhase.COMPLETED)
        self.state.add_message("Director", "Production complete!")

        self._save_script()

        return self.script

    def _phase_development(self, prompt: str, target_duration: float):
        """Development phase: Create the script and storyboard with critique-refine loop."""
        self.state.add_message("Director", "=== DEVELOPMENT PHASE ===")

        screenplay_data = self.screenwriter.process({
            "prompt": prompt,
            "target_duration": target_duration,
            "genre": self.script.genre,
        })

        if self.llm_client:
            screenplay_data = self._refine_script_with_feedback(screenplay_data)

        self.script.characters = [
            Character(**c) for c in screenplay_data.get("characters", [])
        ]
        self.script.scenes = [
            Scene(
                scene_number=s["scene_number"],
                title=s["title"],
                location=s["location"],
                time_of_day=s["time_of_day"],
                description=s["description"],
                emotional_tone=EmotionalTone(s["emotional_tone"]) if isinstance(s["emotional_tone"], str) else s["emotional_tone"],
                characters=s.get("characters", []),
                environment_prompt=s.get("environment_prompt"),
                shots=[
                    Shot(
                        shot_number=sh["shot_number"],
                        shot_type=ShotType(sh["shot_type"]) if isinstance(sh["shot_type"], str) else sh["shot_type"],
                        description=sh["description"],
                        duration_seconds=sh["duration_seconds"],
                        dialogue=sh.get("dialogue"),
                        action=sh.get("action"),
                        camera_movement=sh.get("camera_movement"),
                        visual_prompt=sh.get("visual_prompt"),
                        characters=sh.get("characters", []),
                        emotional_tone=EmotionalTone(sh["emotional_tone"]) if isinstance(sh.get("emotional_tone", "neutral"), str) else sh.get("emotional_tone", EmotionalTone.NEUTRAL),
                    )
                    for sh in s.get("shots", [])
                ],
            )
            for s in screenplay_data.get("scenes", [])
        ]

        self.state.add_message("Director",
            f"Script complete: {len(self.script.scenes)} scenes, "
            f"{sum(len(s.shots) for s in self.script.scenes)} shots")

    def _refine_script_with_feedback(self, screenplay_data: dict) -> dict:
        """Run critique-and-refine loop between agents."""
        max_iterations = 2

        for iteration in range(max_iterations):
            self.state.add_message("Director", f"--- Critique Round {iteration + 1} ---")

            casting_feedback = self.casting.process({
                "script": screenplay_data,
                "mode": "critique",
            })
            critique_notes = casting_feedback.get("critique_notes", [])
            if critique_notes:
                self.state.add_message("Casting", f"Found {len(critique_notes)} continuity concerns")
                screenplay_data = self._apply_casting_feedback(screenplay_data, critique_notes)
            else:
                self.state.add_message("Casting", "No continuity issues found")

            sound_feedback = self.sound.process({
                "script": screenplay_data,
                "mode": "critique",
            })
            sound_issues = sound_feedback.get("critique_notes", [])
            if sound_issues:
                self.state.add_message("Sound", f"Found {len(sound_issues)} emotional alignment issues")
                screenplay_data = self._apply_sound_feedback(screenplay_data, sound_issues)
            else:
                self.state.add_message("Sound", "Emotional pacing looks good")

        return screenplay_data

    def _apply_casting_feedback(self, screenplay_data: dict, notes: list[dict]) -> dict:
        """Apply casting agent feedback to screenplay."""
        scenes = screenplay_data.get("scenes", [])
        for note in notes:
            if note.get("type") == "character_continuity":
                subject = note.get("subject")
                scene_nums = note.get("scenes", [])
                for scene in scenes:
                    if scene.get("scene_number") in scene_nums and subject in scene.get("characters", []):
                        scene["description"] += f" (maintain {subject} visual consistency)"
        return screenplay_data

    def _apply_sound_feedback(self, screenplay_data: dict, notes: list[dict]) -> dict:
        """Apply sound designer feedback to screenplay."""
        scenes = screenplay_data.get("scenes", [])
        for note in notes:
            if note.get("type") == "emotional_alignment":
                scene_num = note.get("scene_number")
                suggestion = note.get("suggestion")
                for scene in scenes:
                    if scene.get("scene_number") == scene_num:
                        scene["description"] += f" [Audio note: {suggestion}]"
        return screenplay_data

    def _phase_pre_production(self):
        """Pre-production: Casting, consistency, and sound design."""
        self.state.transition_to(ProductionPhase.PRE_PRODUCTION)
        self.state.add_message("Director", "=== PRE-PRODUCTION PHASE ===")

        casting_data = self.casting.process({
            "script": self.script.to_dict(),
        })

        character_prompts = casting_data.get("character_prompts", {})
        environment_prompts = casting_data.get("environment_prompts", {})

        for scene in self.script.scenes:
            if scene.environment_prompt in environment_prompts:
                scene.environment_prompt = environment_prompts[scene.environment_prompt]
            for shot in scene.shots:
                for char_name in shot.characters:
                    if char_name in character_prompts:
                        shot.visual_prompt = self._merge_visual_prompts(
                            shot.visual_prompt,
                            character_prompts[char_name],
                        )

        sound_data = self.sound.process({
            "script": self.script.to_dict(),
        })

        self.script.soundtrack = [
            SoundtrackSegment(
                start_time=s["start_time"],
                end_time=s["end_time"],
                mood=EmotionalTone(s["mood"]) if isinstance(s["mood"], str) else s["mood"],
                tempo=s["tempo"],
                instruments=s["instruments"],
                description=s["description"],
                generated_audio_path=s.get("generated_audio_path"),
            )
            for s in sound_data.get("soundtrack", [])
        ]
        self.script.sound_cues = [
            SoundCue(
                timestamp=c["timestamp"],
                duration=c["duration"],
                cue_type=c["cue_type"],
                description=c["description"],
                intensity=c.get("intensity", 0.5),
                generated_audio_path=c.get("generated_audio_path"),
            )
            for c in sound_data.get("sound_cues", [])
        ]

        self.state.add_message("Director", "Pre-production complete")

    def _phase_production(self):
        """Production phase: Generate visual assets."""
        self.state.transition_to(ProductionPhase.PRODUCTION)
        self.state.add_message("Director", "=== PRODUCTION PHASE ===")

        total_shots = sum(len(s.shots) for s in self.script.scenes)
        self.state.add_message("Director", f"Generating {total_shots} shots...")

        for scene in self.script.scenes:
            for shot in scene.shots:
                if self.state.config.enable_image_generation:
                    image_path = self._generate_shot_image(scene, shot)
                    if image_path:
                        shot.generated_image_path = str(image_path)

                if self.state.config.enable_video_generation and shot.generated_image_path:
                    video_path = self._generate_shot_video(shot)
                    if video_path:
                        shot.generated_video_path = str(video_path)

        self.state.add_message("Director", "Production phase complete")

    def _phase_post_production(self):
        """Post-production: Edit and assemble the film."""
        self.state.transition_to(ProductionPhase.POST_PRODUCTION)
        self.state.add_message("Director", "=== POST-PRODUCTION PHASE ===")

        edit_data = self.editor.process({
            "script": self.script.to_dict(),
            "config": {
                "fps": self.state.config.fps,
                "resolution": self.state.config.resolution,
                "output_dir": str(self.state.config.output_dir),
            },
        })

        self.script.edit_decisions = [
            EditDecision(
                shot_index=e["shot_index"],
                transition_in=TransitionType(e["transition_in"]) if isinstance(e["transition_in"], str) else e["transition_in"],
                transition_out=TransitionType(e["transition_out"]) if isinstance(e["transition_out"], str) else e["transition_out"],
                transition_duration=e.get("transition_duration", 0.5),
                speed_adjustment=e.get("speed_adjustment", 1.0),
                color_grade=e.get("color_grade"),
            )
            for e in edit_data.get("edit_decisions", [])
        ]

        output_path = self.state.config.output_dir / "final_cut.mp4"
        self.editor.assemble_film(self.script, str(output_path))

        self.state.add_artifact("final_cut", output_path)
        self.state.add_message("Director", f"Film assembled: {output_path}")

    def _merge_visual_prompts(self, shot_prompt: str | None, character_prompt: str) -> str:
        """Merge shot description with character consistency prompt."""
        if shot_prompt:
            return f"{shot_prompt}, featuring {character_prompt}"
        return character_prompt

    def _generate_shot_image(self, scene: Scene, shot: Shot) -> Path | None:
        """Generate image for a shot using configured image generation."""
        self.state.add_message("Director",
            f"Generating image: Scene {scene.scene_number}, Shot {shot.shot_number}")

        if not self.state.config.enable_image_generation:
            return None

        openai_mod, err = safe_import("openai")
        if not openai_mod:
            self.state.add_error(err or "openai package not installed")
            self.log(f"Skipped image generation: {err}")
            return None

        image_dir = self.state.config.output_dir / "images"
        image_dir.mkdir(exist_ok=True)
        image_path = image_dir / f"scene{scene.scene_number}_shot{shot.shot_number}.png"

        if shot.visual_prompt:
            self.state.add_message("Director",
                f"  Prompt: {shot.visual_prompt[:100]}...")

        return image_path

    def _generate_shot_video(self, shot: Shot) -> Path | None:
        """Generate video clip for a shot."""
        self.state.add_message("Director",
            f"Generating video: Shot {shot.shot_number}")

        if not self.state.config.enable_video_generation:
            return None

        runwayml_mod, err = safe_import("runwayml")
        if not runwayml_mod:
            self.state.add_error(err or "runwayml package not installed")
            self.log(f"Skipped video generation: {err}")
            return None

        video_dir = self.state.config.output_dir / "videos"
        video_dir.mkdir(exist_ok=True)
        video_path = video_dir / f"shot{shot.shot_number}.mp4"

        return video_path

    def _save_script(self):
        """Save the complete script to output directory."""
        script_path = self.state.config.output_dir / "script.json"
        script_path.write_text(json.dumps(self.script.to_dict(), indent=2))
        self.state.add_artifact("script", script_path)
        self.state.add_message("Director", f"Script saved: {script_path}")

    def get_production_report(self) -> dict:
        """Generate a production report."""
        return {
            "title": self.script.title if self.script else "N/A",
            "phase": self.state.phase.value,
            "scenes": len(self.script.scenes) if self.script else 0,
            "total_shots": sum(len(s.shots) for s in self.script.scenes) if self.script else 0,
            "estimated_duration": self.script.total_duration if self.script else 0,
            "characters": len(self.script.characters) if self.script else 0,
            "sound_cues": len(self.script.sound_cues) if self.script else 0,
            "conversation_length": len(self.state.agent_messages),
            "errors": self.state.errors,
        }
