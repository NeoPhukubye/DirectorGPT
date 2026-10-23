# AGENTS.md

This file provides guidance to AI coding agents when working with the DirectorGPT repository.

## Project Overview

DirectorGPT is an AI-powered multi-agent film production studio. It uses specialized AI agents (Screenwriter, Casting, Sound Designer, Editor) orchestrated by a DirectorAgent to produce short films from text prompts.

## Architecture

- **DirectorAgent** (`director_gpt/director.py`) - Central orchestrator
- **ScreenwriterAgent** (`director_gpt/agents/screenwriter.py`) - Script generation & storyboarding
- **CastingAgent** (`director_gpt/agents/casting.py`) - Character/environment consistency
- **SoundDesignerAgent** (`director_gpt/agents/sound.py`) - Soundtrack & foley
- **EditorAgent** (`director_gpt/agents/editor.py`) - Video assembly & transitions

## Code Conventions

- Use Python 3.10+ type hints (PEP 604 union syntax `X | None`)
- Follow the existing code style: 4-space indentation, line length 100
- Use `from __future__ import annotations` when needed for forward references
- All public methods should have docstrings
- Use `# noqa: BLE001` for intentional broad exception catches in fallback code

## Testing

- Run tests: `pytest`
- Tests should be in `tests/` with `test_*.py` naming
- Use `tmp_path` fixture for filesystem operations
- Use `MagicMock` for mocking LLM clients

## Linting & Formatting

- `black` for formatting (line-length=100)
- `ruff` for linting (E, W, F, I, B, C4, UP)
- `mypy` for type checking
- All three must pass before committing

## Dependencies

- Core: pydantic, rich, click, google-generativeai, fastapi, uvicorn
- Optional extras: `[image,audio,video]` for media generation
- FFmpeg is required for video assembly