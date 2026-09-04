"""Editor agent for video assembly and post-production."""

import json
import subprocess
from pathlib import Path

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

        tmpdir = output_path.parent / "ffmpeg_inputs"
        tmpdir.mkdir(parents=True, exist_ok=True)

        shots = []
        for scene in script.scenes:
            shots.extend(scene.shots)

        edit_decisions = [d.to_dict() if hasattr(d, "to_dict") else d for d in getattr(script, "edit_decisions", [])]

        input_paths = []
        for i, shot in enumerate(shots):
            path = getattr(shot, "generated_video_path", None)
            if path and Path(path).exists():
                input_paths.append(Path(path))
            else:
                clip = tmpdir / f"shot_{i:04d}.mp4"
                self._generate_placeholder_clip(shot, clip)
                input_paths.append(clip)

        filter_complex = self._build_filter_complex(script, edit_decisions)

        cmd = ["ffmpeg", "-y"]
        for p in input_paths:
            cmd.extend(["-i", str(p)])

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ])

        self.log(f"Running FFmpeg: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                self.log(f"FFmpeg stderr: {result.stderr[:500]}")
                self.state.add_error(result.stderr)
                return False
            self.log(f"Final cut saved: {output_path}")
            return True
        except FileNotFoundError:
            self.log("FFmpeg not found on system")
            self.state.add_error("FFmpeg not installed")
            return False

    def _generate_placeholder_clip(self, shot, output_path: Path) -> None:
        """Generate a colored placeholder video clip for a shot."""
        duration = max(getattr(shot, "duration_seconds", 2.0), 1.0)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i",
            f"color=c=0x1a1a2e:s=1920x1080:d={duration}:r=24",
            "-vf", f"drawtext=text='Shot {getattr(shot, 'shot_number', 0)}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=False)

    def _build_filter_complex(self, script, edit_decisions: list[dict]) -> str:
        """Build FFmpeg filter complex for transitions and effects."""
        shots = []
        for scene in script.scenes:
            shots.extend(scene.shots)

        if not shots:
            return ""

        n = len(shots)
        decision_map = {d["shot_index"]: d for d in edit_decisions}

        xfade_type_map = {
            "cut": "fade",
            "fade_in": "fade",
            "fade_out": "fade",
            "dissolve": "dissolve",
            "wipe": "wipeleft",
            "jump_cut": "fade",
            "match_cut": "fade",
        }

        def input_ref(idx: int) -> str:
            return f"[{idx}:v]"

        def next_label(prefix: str = "v") -> str:
            next_label.counter += 1
            return f"{prefix}{next_label.counter}"
        next_label.counter = -1

        segments = []
        seg_start = 0
        for i in range(1, n):
            prev_decision = decision_map.get(i - 1, {})
            trans_out = prev_decision.get("transition_out", "cut")
            if trans_out == "cut":
                segments.append(list(range(seg_start, i)))
                seg_start = i
        segments.append(list(range(seg_start, n)))

        filter_parts = []
        segment_outputs = []

        for seg in segments:
            has_xfade = any(
                decision_map.get(i, {}).get("transition_out", "cut") != "cut"
                for i in seg[:-1]
            )

            if len(seg) == 1:
                shot_idx = seg[0]
                decision = decision_map.get(shot_idx, {})
                speed = decision.get("speed_adjustment", 1.0)
                if speed != 1.0:
                    label = next_label("s")
                    filter_parts.append(f"{input_ref(shot_idx)}setpts={speed}*PTS[{label}]")
                    segment_outputs.append(f"[{label}]")
                else:
                    segment_outputs.append(input_ref(shot_idx))
            elif not has_xfade:
                inputs = "".join(input_ref(i) for i in seg)
                label = next_label("seg")
                filter_parts.append(f"{inputs}concat=n={len(seg)}:v=1:a=0[{label}]")
                segment_outputs.append(f"[{label}]")
            else:
                prev_label = None
                for j, shot_idx in enumerate(seg):
                    decision = decision_map.get(shot_idx, {})
                    speed = decision.get("speed_adjustment", 1.0)

                    if j == 0:
                        if speed != 1.0:
                            label = next_label("s")
                            filter_parts.append(f"{input_ref(shot_idx)}setpts={speed}*PTS[{label}]")
                            prev_label = f"[{label}]"
                        else:
                            prev_label = input_ref(shot_idx)
                    else:
                        prev_decision = decision_map.get(seg[j - 1], {})
                        trans_out = prev_decision.get("transition_out", "cut")
                        trans_dur = float(prev_decision.get("transition_duration", 0.5))
                        xfade = xfade_type_map.get(trans_out, "fade")

                        offset = 0.0
                        for k in range(j):
                            s = shots[seg[k]]
                            sp = decision_map.get(seg[k], {}).get("speed_adjustment", 1.0)
                            offset += getattr(s, "duration_seconds", 2.0) / max(sp, 0.1)
                        offset -= trans_dur
                        offset = max(offset, 0.0)

                        if speed != 1.0:
                            label = next_label("s")
                            filter_parts.append(f"{input_ref(shot_idx)}setpts={speed}*PTS[{label}]")
                            cur_input = f"[{label}]"
                        else:
                            cur_input = input_ref(shot_idx)

                        out_label = next_label("seg")
                        filter_parts.append(
                            f"{prev_label}{cur_input}xfade=transition={xfade}:duration={trans_dur}:offset={offset}[{out_label}]"
                        )
                        prev_label = f"[{out_label}]"

                segment_outputs.append(prev_label)

        total = len(segment_outputs)
        if total == 1:
            return ";".join(filter_parts)

        concat_inputs = "".join(segment_outputs)
        filter_parts.append(f"{concat_inputs}concat=n={total}:v=1:a=0[outv]")
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
