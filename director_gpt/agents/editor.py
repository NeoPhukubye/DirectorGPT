"""Editor agent for video assembly and post-production."""

import os
import subprocess
from pathlib import Path
from typing import Any

from director_gpt.agents import BaseAgent
from director_gpt.models import EditDecision, TransitionType
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

    def _get_color_grade(self, emotional_tone: str) -> str | None:
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
            "# Step 1: Prepare clips and build filter_complex"
        )

        commands.append(
            "# Step 2: Concatenate with transitions and color grading"
        )

        commands.append(
            "# Step 3: Mix audio tracks"
        )

        commands.append(
            "# Step 4: Final output"
        )

        return commands

    def assemble_film(self, script, output_path: str) -> bool:
        """Assemble the final film using FFmpeg."""
        self.log("Starting film assembly")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        renderer = VideoRenderer(str(output_path.parent / "rendered"))
        result_path = renderer.stitch_production(script.to_dict(), script.title)
        self.log(f"Final cut saved: {result_path}")
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
                        f'cp "{shot.generated_video_path}" "$TMPDIR/shot_{shot_index:04d}.mp4"'
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


class VideoRenderer:
    """Renders a stitched MP4 from project metadata using FFmpeg."""

    def __init__(self, output_dir: str = "output/rendered"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def stitch_production(self, project_data: dict[str, Any], project_name: str) -> str:
        """
        Takes project JSON (with shots, soundtrack, and edit_decisions)
        and renders a final stitched MP4 using FFmpeg.
        """
        scenes = project_data.get("scenes", [])
        edit_decisions = project_data.get("edit_decisions", [])
        soundtrack = project_data.get("soundtrack", [])

        shots: list[dict[str, Any]] = []
        for scene in scenes:
            shots.extend(scene.get("shots", []))

        if not shots:
            raise ValueError("No shots found in project data.")

        clip_files = []

        for idx, shot in enumerate(shots):
            duration = shot.get("duration_seconds", 5)
            video_path = shot.get("generated_video_path")
            image_path = shot.get("generated_image_path")

            decision = next((d for d in edit_decisions if d.get("shot_index") == idx), {})
            trans_in = decision.get("transition_in")
            trans_out = decision.get("transition_out")
            trans_dur = decision.get("transition_duration", 0.5)

            shot_out_path = self.output_dir / f"temp_shot_{idx:02d}.mp4"

            filters = [
                "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
            ]
            if trans_in == "fade_in":
                filters.append(f"fade=t=in:st=0:d={trans_dur}")
            if trans_out == "fade_out":
                start_fade = max(0.0, float(duration) - float(trans_dur))
                filters.append(f"fade=t=out:st={start_fade}:d={trans_dur}")

            filter_chain = ",".join(filters)

            if video_path and os.path.exists(video_path):
                cmd = [
                    "ffmpeg", "-y", "-i", video_path,
                    "-vf", filter_chain,
                    "-t", str(duration),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(shot_out_path),
                ]
            elif image_path and os.path.exists(image_path):
                cmd = [
                    "ffmpeg", "-y", "-loop", "1", "-i", image_path,
                    "-vf", filter_chain,
                    "-t", str(duration),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(shot_out_path),
                ]
            else:
                shot_desc = shot.get("description", f"Shot {idx + 1}")
                text_filter = f"drawtext=text='{shot_desc}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2"
                cmd = [
                    "ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"color=c=black:s=1920x1080:d={duration}",
                    "-vf", f"{filter_chain},{text_filter}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(shot_out_path),
                ]

            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            clip_files.append(shot_out_path)

        concat_list_path = self.output_dir / "concat_list.txt"
        with open(concat_list_path, "w") as f:
            f.writelines(f"file '{clip.resolve()}'\n" for clip in clip_files)

        raw_stitched_video = self.output_dir / "video_assembled.mp4"
        concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list_path),
            "-c", "copy",
            str(raw_stitched_video),
        ]
        subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        final_mp4 = self.output_dir / f"{project_name}_final_cut.mp4"

        audio_inputs = []
        for stem in soundtrack:
            stem_path = stem.get("generated_audio_path")
            if stem_path and os.path.exists(stem_path):
                audio_inputs.append(stem_path)

        if audio_inputs:
            mix_cmd = [
                "ffmpeg", "-y", "-i", str(raw_stitched_video),
                "-i", audio_inputs[0],
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(final_mp4),
            ]
            subprocess.run(mix_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            raw_stitched_video.rename(final_mp4)

        if concat_list_path.exists():
            concat_list_path.unlink()
        for clip in clip_files:
            if clip.exists():
                clip.unlink()

        return str(final_mp4)
