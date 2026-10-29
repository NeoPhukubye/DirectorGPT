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
    FilmScript,
    Scene,
    Shot,
    SoundCue,
    SoundtrackSegment,
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

    def produce_film(
        self,
        prompt: str,
        title: str = "Untitled",
        genre: str = "drama",
        target_duration: float = 60.0,
    ) -> FilmScript:
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
        assert self.script is not None, "Script must be initialized before development phase"
        self.state.add_message("Director", "=== DEVELOPMENT PHASE ===")

        screenplay_data = self.screenwriter.process(
            {
                "prompt": prompt,
                "target_duration": target_duration,
                "genre": self.script.genre,
            }
        )

        if self.llm_client:
            screenplay_data = self._refine_script_with_feedback(screenplay_data)

        self.script.characters = [
            Character.from_dict(c) for c in screenplay_data.get("characters", [])
        ]
        self.script.scenes = [Scene.from_dict(s) for s in screenplay_data.get("scenes", [])]

        self.state.add_message(
            "Director",
            f"Script complete: {len(self.script.scenes)} scenes, "
            f"{sum(len(s.shots) for s in self.script.scenes)} shots",
        )

    def _refine_script_with_feedback(self, screenplay_data: dict) -> dict:
        """Run critique-and-refine loop between agents."""
        max_iterations = 2

        for iteration in range(max_iterations):
            self.state.add_message("Director", f"--- Critique Round {iteration + 1} ---")

            casting_feedback = self.casting.process(
                {
                    "script": screenplay_data,
                    "mode": "critique",
                }
            )
            critique_notes = casting_feedback.get("critique_notes", [])
            if critique_notes:
                self.state.add_message(
                    "Casting", f"Found {len(critique_notes)} continuity concerns"
                )
                screenplay_data = self._apply_casting_feedback(screenplay_data, critique_notes)
            else:
                self.state.add_message("Casting", "No continuity issues found")

            sound_feedback = self.sound.process(
                {
                    "script": screenplay_data,
                    "mode": "critique",
                }
            )
            sound_issues = sound_feedback.get("critique_notes", [])
            if sound_issues:
                self.state.add_message(
                    "Sound", f"Found {len(sound_issues)} emotional alignment issues"
                )
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
                    if scene.get("scene_number") in scene_nums and subject in scene.get(
                        "characters", []
                    ):
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

        casting_data = self.casting.process(
            {
                "script": self.script.to_dict(),
            }
        )

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

        sound_data = self.sound.process(
            {
                "script": self.script.to_dict(),
            }
        )

        self.script.soundtrack = [
            SoundtrackSegment.from_dict(s) for s in sound_data.get("soundtrack", [])
        ]
        self.script.sound_cues = [SoundCue.from_dict(c) for c in sound_data.get("sound_cues", [])]

        if self.state.config.enable_audio_generation:
            self.state.add_message("Director", "Generating audio assets...")
            try:
                audio_result = self.sound.generate_audio_assets(self.script.to_dict())
                if audio_result.get("generated"):
                    self.state.add_message(
                        "Director",
                        f"Audio generation complete: {len(audio_result.get('soundtrack', []))} tracks, "
                        f"{len(audio_result.get('sound_cues', []))} cues",
                    )
                else:
                    self.log(f"Audio generation skipped: {audio_result.get('error', 'unknown')}")
            except Exception as e:  # noqa: BLE001 - intentional broad catch for audio generation
                self.state.add_error(f"Audio generation failed: {e}")
                self.log(f"  Audio generation failed: {e}")

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
                    try:
                        image_path = self._generate_shot_image(scene, shot)
                        if image_path:
                            shot.generated_image_path = str(image_path)
                    except Exception as e:  # noqa: BLE001 - intentional broad catch for generation
                        self.state.add_error(f"Image generation failed: {e}")
                        self.log(f"  Image generation failed: {e}")

                if self.state.config.enable_video_generation:
                    try:
                        video_path = self._generate_shot_video(shot)
                        if video_path:
                            shot.generated_video_path = str(video_path)
                    except Exception as e:  # noqa: BLE001 - intentional broad catch for generation
                        self.state.add_error(f"Video generation failed: {e}")
                        self.log(f"  Video generation failed: {e}")

        self.state.add_message("Director", "Production phase complete")

    def _phase_post_production(self):
        """Post-production: Edit and assemble the film."""
        self.state.transition_to(ProductionPhase.POST_PRODUCTION)
        self.state.add_message("Director", "=== POST-PRODUCTION PHASE ===")

        edit_data = self.editor.process(
            {
                "script": self.script.to_dict(),
                "config": {
                    "fps": self.state.config.fps,
                    "resolution": self.state.config.resolution,
                    "output_dir": str(self.state.config.output_dir),
                },
            }
        )

        self.script.edit_decisions = [
            EditDecision.from_dict(e) for e in edit_data.get("edit_decisions", [])
        ]

        try:
            output_path = self.state.config.output_dir / "final_cut.mp4"
            actual_output = self.editor.assemble_film(self.script, str(output_path))

            self.state.add_artifact("final_cut", Path(actual_output))
            self.state.add_message("Director", f"Film assembled: {actual_output}")
        except RuntimeError as e:
            self.state.add_error(f"Film assembly failed: {e}")
            self.log(f"  Film assembly failed: {e}")

    def _merge_visual_prompts(self, shot_prompt: str | None, character_prompt: str) -> str:
        """Merge shot description with character consistency prompt."""
        if shot_prompt:
            return f"{shot_prompt}, featuring {character_prompt}"
        return character_prompt

    def _generate_shot_image(self, scene: Scene, shot: Shot) -> Path | None:
        """Generate image for a shot using configured image generation."""
        self.state.add_message(
            "Director", f"Generating image: Scene {scene.scene_number}, Shot {shot.shot_number}"
        )

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

        if image_path.exists():
            self.log(f"  Image already exists: {image_path}")
            return image_path

        if not shot.visual_prompt:
            self.log("  No visual prompt provided, skipping image generation")
            return None

        try:
            import os

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                self.state.add_error("OPENAI_API_KEY not set")
                return None

            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            prompt = shot.visual_prompt
            self.state.add_message("Director", f"  Prompt: {prompt[:100]}...")

            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                n=1,
            )

            image_url = response.data[0].url
            import urllib.request

            urllib.request.urlretrieve(image_url, image_path)
            self.log(f"  Image saved: {image_path}")
            return image_path

        except Exception as e:  # noqa: BLE001 - intentional broad catch for generation fallback
            self.state.add_error(f"Image generation failed: {e}")
            self.log(f"  Image generation failed: {e}")
            return None

    def _generate_shot_video(self, shot: Shot) -> Path | None:
        """Generate video clip for a shot using RunwayML text-to-video."""
        self.state.add_message("Director", f"Generating video: Shot {shot.shot_number}")

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

        if video_path.exists():
            self.log(f"  Video already exists: {video_path}")
            return video_path

        try:
            import os

            api_key = os.getenv("RUNWAYML_API_SECRET")
            if not api_key:
                self.state.add_error("RUNWAYML_API_SECRET not set")
                return None

            from runwayml import RunwayML

            client = RunwayML(api_key=api_key)

            prompt_text = shot.visual_prompt or shot.description or f"Shot {shot.shot_number}"
            ratio = f"{self.state.config.resolution[0]}:{self.state.config.resolution[1]}"
            duration = min(max(int(shot.duration_seconds), 1), 10)

            self.state.add_message("Director", f"  Prompt: {prompt_text[:100]}...")

            # Use text-to-video generation (no input image required)
            task = client.image_to_video.create(
                model="gen4_turbo",
                prompt_text=prompt_text,
                ratio=ratio,
                duration=duration,
            ).wait_for_task_output()

            if task and hasattr(task, "output") and task.output:
                video_url = task.output.url if hasattr(task.output, "url") else task.output
                if isinstance(video_url, list):
                    video_url = video_url[0]
                import urllib.request

                urllib.request.urlretrieve(video_url, video_path)
                self.log(f"  Video saved: {video_path}")
                return video_path
            else:
                self.state.add_error("Video generation failed: no output")
                return None

        except Exception as e:  # noqa: BLE001 - intentional broad catch for generation fallback
            self.state.add_error(f"Video generation failed: {e}")
            self.log(f"  Video generation failed: {e}")
            return None

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
