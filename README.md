# DirectorGPT

**AI-powered multi-agent film production studio**

DirectorGPT is a collaborative multi-agent system where specialized AI agents work together to produce short films. Each agent handles a specific aspect of film production, from screenwriting to final editing.

## Architecture

```
DirectorGPT
├── DirectorAgent (Orchestrator)
│   ├── ScreenwriterAgent   → Scripts & Storyboards
│   ├── CastingAgent        → Character/Environment Consistency
│   ├── SoundDesignerAgent  → Soundtrack & Foley
│   └── EditorAgent         → Video Assembly & Transitions
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Screenwriter** | Deconstructs prompts into scenes, character arcs, shot-by-shot storyboards |
| **Casting/Consistency** | Maintains character and environment visual embeddings across scenes |
| **Sound Designer** | Analyzes emotional cues to generate timed scores and sound effects |
| **Editor** | Cuts, transitions, and stitches video segments into rendered MP4 |

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/DirectorGPT.git
cd DirectorGPT

# Install with pip
pip install -e .

# Or install with extras for media generation
pip install -e ".[image,audio,video]"
```

## Quick Start

### Generate a Full Film

```bash
directorgpt produce "A detective receives a mysterious phone call that changes everything" \
  --title "The Call" \
  --genre drama \
  --duration 90 \
  --output ./output/the_call
```

### Generate Script Only

```bash
directorgpt script "Two strangers meet on a train and share a life-changing conversation" \
  --genre romance \
  --duration 60
```

### View Production Report

```bash
directorgpt report --output ./output/the_call
```

## Examples

```bash
# Horror short
directorgpt produce "A family moves into a house where the walls whisper at night" \
  --title "Whispers" \
  --genre horror \
  --duration 120

# Sci-fi concept
directorgpt produce "An astronaut discovers an abandoned station with a still-functioning AI" \
  --title "Ghost Station" \
  --genre sci-fi \
  --duration 90

# Comedy sketch
directorgpt produce "A job interview where everything that can go wrong does" \
  --title "The Interview" \
  --genre comedy \
  --duration 45
```

## Output Structure

```
output/
└── the_call/
    ├── script.json          # Complete film script with all metadata
    ├── project_state.json   # Production state and conversation log
    ├── final_cut.mp4        # Rendered final film (requires video generation)
    ├── images/              # Generated shot images
    ├── videos/              # Generated shot videos
    └── audio/               # Generated audio assets
```

## Configuration

Create a `config.json` for API keys and generation settings:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "sk-..."
  },
  "image_gen": {
    "provider": "dall-e-3",
    "size": "1920x1080"
  },
  "audio": {
    "provider": "elevenlabs",
    "api_key": "..."
  },
  "video": {
    "provider": "runway",
    "api_key": "..."
  }
}
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black director_gpt/ tests/
ruff check director_gpt/ tests/

# Type check
mypy director_gpt/
```

## Media Generation

DirectorGPT supports optional AI-powered media generation:

- **Image Generation** (`--enable-images`): Uses DALL-E 3 to generate storyboard frames
- **Video Generation** (`--enable-video`): Uses RunwayML Gen-4 to generate video clips
- **Audio Generation** (`--enable-audio`): Uses ElevenLabs for soundtrack and sound effects

Set the following environment variables:
- `OPENAI_API_KEY` - For DALL-E image generation
- `RUNWAYML_API_SECRET` - For RunwayML video generation
- `ELEVENLABS_API_KEY` - For ElevenLabs audio generation

## Configuration

Create a `config.json` for API keys and generation settings:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "sk-..."
  },
  "image_gen": {
    "provider": "dall-e-3",
    "size": "1920x1080"
  },
  "audio": {
    "provider": "elevenlabs",
    "api_key": "..."
  },
  "video": {
    "provider": "runway",
    "api_key": "..."
  }
}
```

## License

MIT
