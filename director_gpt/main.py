"""Main CLI entry point for DirectorGPT."""

import argparse
import json
import sys
from pathlib import Path

from director_gpt.director import DirectorAgent
from director_gpt.models.project import ProjectConfig, ProjectState


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="directorgpt",
        description="DirectorGPT - AI-powered multi-agent film production studio",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    produce_parser = subparsers.add_parser("produce", help="Produce a short film")
    produce_parser.add_argument(
        "prompt",
        help="High-level film prompt or concept",
    )
    produce_parser.add_argument(
        "--title", "-t",
        default="Untitled",
        help="Film title",
    )
    produce_parser.add_argument(
        "--genre", "-g",
        default="drama",
        choices=["drama", "horror", "comedy", "sci-fi", "romance", "thriller"],
        help="Film genre",
    )
    produce_parser.add_argument(
        "--duration", "-d",
        type=float,
        default=60.0,
        help="Target duration in seconds",
    )
    produce_parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory",
    )
    produce_parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Frames per second",
    )
    produce_parser.add_argument(
        "--resolution",
        default="1920x1080",
        help="Video resolution (WxH)",
    )
    produce_parser.add_argument(
        "--enable-images",
        action="store_true",
        help="Enable image generation (requires API key)",
    )
    produce_parser.add_argument(
        "--enable-video",
        action="store_true",
        help="Enable video generation (requires API key)",
    )
    produce_parser.add_argument(
        "--enable-audio",
        action="store_true",
        help="Enable audio generation (requires API key)",
    )

    script_parser = subparsers.add_parser("script", help="Generate script only")
    script_parser.add_argument("prompt", help="Film prompt")
    script_parser.add_argument("--genre", "-g", default="drama")
    script_parser.add_argument("--duration", "-d", type=float, default=60.0)
    script_parser.add_argument("--output", "-o", default="./output")

    report_parser = subparsers.add_parser("report", help="Show production report")
    report_parser.add_argument("--output", "-o", default="./output")

    return parser


def cmd_produce(args):
    """Execute film production pipeline."""
    width, height = map(int, args.resolution.split("x"))

    config = ProjectConfig(
        project_name=args.title,
        output_dir=Path(args.output),
        fps=args.fps,
        resolution=(width, height),
        enable_image_generation=args.enable_images,
        enable_video_generation=args.enable_video,
        enable_audio_generation=args.enable_audio,
    )

    state = ProjectState(config=config)
    director = DirectorAgent(state)

    print(f"\n{'='*60}")
    print(f"  DirectorGPT - Film Production Studio")
    print(f"{'='*60}")
    print(f"\n  Title: {args.title}")
    print(f"  Genre: {args.genre}")
    print(f"  Target Duration: {args.duration}s")
    print(f"  Output: {config.output_dir}")
    print(f"\n{'='*60}\n")

    script = director.produce_film(
        prompt=args.prompt,
        title=args.title,
        genre=args.genre,
        target_duration=args.duration,
    )

    report = director.get_production_report()

    print(f"\n{'='*60}")
    print(f"  Production Complete!")
    print(f"{'='*60}")
    print(f"\n  Scenes: {report['scenes']}")
    print(f"  Total Shots: {report['total_shots']}")
    print(f"  Characters: {report['characters']}")
    print(f"  Estimated Duration: {report['estimated_duration']:.1f}s")
    print(f"  Sound Cues: {report['sound_cues']}")
    print(f"\n  Output Files:")
    for name, path in state.artifacts.items():
        print(f"    - {name}: {path}")
    print(f"\n{'='*60}\n")

    state.save_state()

    return 0


def cmd_script(args):
    """Generate script only."""
    from director_gpt.agents.screenwriter import ScreenwriterAgent

    config = ProjectConfig(
        project_name="script_gen",
        output_dir=Path(args.output),
    )
    state = ProjectState(config=config)
    screenwriter = ScreenwriterAgent("Screenwriter", state)

    result = screenwriter.process({
        "prompt": args.prompt,
        "target_duration": args.duration,
        "genre": args.genre,
    })

    output_path = config.output_dir / "script_only.json"
    output_path.write_text(json.dumps(result, indent=2))

    print(f"\nScript generated: {output_path}")
    print(f"Scenes: {len(result.get('scenes', []))}")
    print(f"Characters: {len(result.get('characters', []))}")

    return 0


def cmd_report(args):
    """Show production report."""
    config = ProjectConfig(
        project_name="report",
        output_dir=Path(args.output),
    )
    state = ProjectState.load_state(config)

    print(f"\n{'='*60}")
    print(f"  Production Report")
    print(f"{'='*60}")
    print(f"\n  Phase: {state.phase.value}")
    print(f"  Messages: {len(state.agent_messages)}")
    print(f"  Artifacts: {len(state.artifacts)}")
    print(f"  Errors: {len(state.errors)}")

    if state.agent_messages:
        print(f"\n  Recent Activity:")
        for msg in state.agent_messages[-10:]:
            print(f"    [{msg.get('phase', '?')}] {msg['agent']}: {msg['message'][:60]}")

    print(f"\n{'='*60}\n")

    return 0


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    commands = {
        "produce": cmd_produce,
        "script": cmd_script,
        "report": cmd_report,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
