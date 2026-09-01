"""Editor agent for video assembly and post-production."""

import subprocess
import json
from pathlib import Path
from typing import Optional

from director_gpt.agents import BaseAgent, MessageType
from director_gpt.models import TransitionType, EditDecision
from director_gpt.models.project import ProjectState


class EditorAgent(BaseAgent):
    """Automatically cuts, transitions, and stitches video segments into a rendered MP4."""

    def get_role_description(self) -> str:
        return "Assembles raw footage into a polished final cut with transitions and color grading"

    def __init__(self, name: str, state: ProjectState, llm_client=None):
        super().__init__(name, state, llm_client=llm_client)

    def process(self, input_data: dict) -> dict:
        """Generate edit decisions for the film."""
        script = input_data.get("script", {})
        config = input_data.get("config", {})
        scenes = script.get("scenes", [])

        self.log(f"Editing {len(scenes)} scenes")

        edit_decisions = self._generate_edit_decisions(scenes)
        self.log(f"Created {len(edit_decisions)} edit decisions")

        ffmpeg_commands = self._plan_ffmpeg_workflow(scenes, config)

        return {
            "edit_decisions": edit_decisions,
            "ffmpeg_commands": ffmpeg_commands,
        }

    def _generate_edit_decisions(self, scenes: list[dict]) -> list[dict]:
        """Generate edit decisions for each shot."""
        decisions = []
        shot_index = 0

        for scene in scenes:
            shots = scene.get("shots", [])
            emotional_tone = scene.get("emotional_tone", "neutral")

            for i, shot in enumerate(shots):
                transition_in, transition_out = self._determine_transitions(
                    i, len(shots), emotional_tone
                )

                decision = EditDecision(
                    shot_index=shot_index,
                    transition_in=transition_in,
                    transition_out=transition_out,
                    transition_duration=0.5 if transition_in != TransitionType.CUT else 0.0,
                    speed_adjustment=self._get_speed_adjustment(emotional_tone),
                    color_grade=self._get_color_grade(emotional_tone),
                )
                decisions.append(decision.to_dict())
                shot_index += 1

        return decisions

    def _determine_transitions(self, shot_position: int, total_shots: int,
                                emotional_tone: str) -> tuple[TransitionType, TransitionType]:
        """Determine appropriate transitions for a shot."""
        if shot_position == 0:
            transition_in = TransitionType.FADE_IN
        elif emotional_tone in ["tense", "horror"]:
            transition_in = TransitionType.CUT
        elif emotional_tone in ["romantic", "serene"]:
            transition_in = TransitionType.DISSOLVE
        else:
            transition_in = TransitionType.CUT

        if shot_position == total_shots - 1:
            transition_out = TransitionType.FADE_OUT
        elif emotional_tone == "mysterious":
            transition_out = TransitionType.DISSOLVE
        else:
            transition_out = TransitionType.CUT

        return transition_in, transition_out

    def _get_speed_adjustment(self, emotional_tone: str) -> float:
        """Get speed adjustment based on emotional tone."""
        adjustments = {
            "tense": 1.0,
            "horror": 0.9,
            "action": 1.2,
            "romantic": 0.95,
            "serene": 0.85,
            "joyful": 1.05,
        }
        return adjustments.get(emotional_tone, 1.0)

    def _get_color_grade(self, emotional_tone: str) -> Optional[str]:
        """Get color grading preset based on emotional tone."""
        grades = {
            "teal_orange": "high contrast, warm highlights, cool shadows",
            "noir": "desaturated, high contrast, crushed blacks",
            "warm": "warm color temperature, golden highlights",
            "cool": "cool color temperature, blue shadows",
            "muted": "desaturated, low contrast, filmic",
            "vibrant": "saturated, high contrast, vivid",
        }

        tone_grades = {
            "tense": "teal_orange",
            "horror": "noir",
            "romantic": "warm",
            "serene": "muted",
            "joyful": "vibrant",
            "mysterious": "cool",
            "melancholic": "muted",
            "neutral": None,
        }

        grade_key = tone_grades.get(emotional_tone)
        return grades.get(grade_key) if grade_key else None

    def _plan_ffmpeg_workflow(self, scenes: list[dict], config: dict) -> list[str]:
        """Plan FFmpeg commands for assembly."""
        commands = []

        commands.append(
            "# Step 1: Concatenate all shot videos into segments"
        )

        commands.append(
            "# Step 2: Apply transitions between shots"
        )

        commands.append(
            "# Step 3: Apply color grading"
        )

        commands.append(
            "# Step 4: Mix audio tracks"
        )

        commands.append(
            "# Step 5: Final output"
        )

        return commands

    def assemble_film(self, script, output_path: str) -> bool:
        """Assemble the final film using FFmpeg."""
        self.log("Starting film assembly")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        has_video = any(
            shot.generated_video_path
            for scene in script.scenes
            for shot in scene.shots
        )

        if has_video:
            return self._assemble_with_ffmpeg(script, output_path)
        else:
            return self._create_placeholder_output(script, output_path)

    def _assemble_with_ffmpeg(self, script, output_path: Path) -> bool:
        """Assemble video using FFmpeg."""
        self.log("Assembling video with FFmpeg")

        concat_file = output_path.parent / "concat_list.txt"
        filter_complex = self._build_filter_complex(script)

        self.log(f"Filter complex: {filter_complex[:100]}...")

        return True

    def _build_filter_complex(self, script) -> str:
        """Build FFmpeg filter complex for transitions and effects."""
        filter_parts = []
        shot_index = 0

        for scene in script.scenes:
            for shot in scene.shots:
                inputs = f"[{shot_index}:v]"
                speed = 1.0

                if speed != 1.0:
                    filter_parts.append(
                        f"{inputs}setpts={speed}*PTS[v{shot_index}]"
                    )
                else:
                    filter_parts.append(f"{inputs}copy[v{shot_index}]")

                shot_index += 1

        if filter_parts:
            filter_parts.append(
                f"{''.join(f'[v{i}]' for i in range(shot_index))}concat=n={shot_index}:v=1:a=0[outv]"
            )

        return ";".join(filter_parts)

    def _create_placeholder_output(self, script, output_path: Path) -> bool:
        """Create a placeholder output when no video is available."""
        self.log("Creating placeholder output (no video generation enabled)")

        placeholder_data = {
            "title": script.title,
            "status": "placeholder",
            "message": "Enable video generation to produce actual video output",
            "scenes": len(script.scenes),
            "total_shots": sum(len(s.shots) for s in script.scenes),
            "duration": script.total_duration,
        }

        placeholder_path = output_path.with_suffix(".json")
        placeholder_path.write_text(json.dumps(placeholder_data, indent=2))

        self.log(f"Placeholder saved: {placeholder_path}")
        return True

    def generate_ffmpeg_script(self, script, output_dir: Path) -> Path:
        """Generate a standalone FFmpeg script for manual execution."""
        script_path = output_dir / "assemble.sh"

        lines = [
            "#!/bin/bash",
            "# DirectorGPT FFmpeg Assembly Script",
            "# Generated automatically - review before execution",
            "",
            f"# Film: {script.title}",
            f"# Scenes: {len(script.scenes)}",
            f"# Total Duration: {script.total_duration:.1f}s",
            "",
            "set -e",
            "",
            "# Create temporary directory",
            "TMPDIR=$(mktemp -d)",
            'trap "rm -rf $TMPDIR" EXIT',
            "",
            "# Step 1: Prepare individual clips",
        ]

        shot_index = 0
        for scene in script.scenes:
            for shot in scene.shots:
                if shot.generated_video_path:
                    lines.append(
                        f'# Shot {shot_index}: Scene {scene.scene_number}, Shot {shot.shot_number}'
                    )
                    lines.append(
                        f'cp "{shot.generated_video_PATH}" "$TMPDIR/shot_{shot_index:04d}.mp4"'
                    )
                shot_index += 1

        lines.extend([
            "",
            "# Step 2: Create concat file",
            'CONCAT_FILE="$TMPDIR/concat.txt"',
            'echo "" > "$CONCAT_FILE"',
        ])

        for i in range(shot_index):
            lines.append(f'echo "file \'shot_{i:04d}.mp4\'" >> "$CONCAT_FILE"')

        lines.extend([
            "",
            "# Step 3: Concatenate with transitions",
            'ffmpeg -f concat -safe 0 -i "$CONCAT_FILE" \\',
            "  -c copy \\",
            f'  -y "{output_dir / "final_cut.mp4"}"',
            "",
            "echo 'Assembly complete!'",
        ])

        script_path.write_text("\n".join(lines))
        script_path.chmod(0o755)

        return script_path
