"""FastAPI backend for DirectorGPT web deployment."""

import json
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from director_gpt.director import DirectorAgent
from director_gpt.llm import LLMClient
from director_gpt.models.project import ProjectConfig, ProjectState
from director_gpt.utils.config import LLMConfig

app = FastAPI(
    title="DirectorGPT API",
    description="AI-powered multi-agent film production studio API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://neophukubye.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProduceRequest(BaseModel):
    prompt: str
    title: str = "Untitled"
    genre: str = "drama"
    duration: float = 60.0
    fps: int = 24
    resolution: str = "1920x1080"
    enable_images: bool = False
    enable_video: bool = False
    enable_audio: bool = False
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.0-flash"
    llm_api_key: str | None = None

    @field_validator("duration")
    @classmethod
    def _validate_duration(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("duration must be positive")
        return value

    @field_validator("fps")
    @classmethod
    def _validate_fps(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("fps must be positive")
        return value


class ScriptRequest(BaseModel):
    prompt: str
    genre: str = "drama"
    duration: float = 60.0
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.0-flash"
    llm_api_key: str | None = None

    @field_validator("duration")
    @classmethod
    def _validate_duration(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("duration must be positive")
        return value


def _parse_resolution(resolution: str) -> tuple[int, int]:
    try:
        width, height = resolution.split("x")
        return int(width), int(height)
    except (ValueError, AttributeError) as exc:
        raise HTTPException(
            status_code=422, detail=f"Invalid resolution '{resolution}', expected WxH"
        ) from exc


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/produce")
async def produce(req: ProduceRequest):
    try:
        width, height = _parse_resolution(req.resolution)
        api_key = req.llm_api_key or os.getenv("GEMINI_API_KEY")

        with tempfile.TemporaryDirectory() as tmpdir:
            config = ProjectConfig(
                project_name=req.title,
                output_dir=Path(tmpdir),
                fps=req.fps,
                resolution=(width, height),
                enable_image_generation=req.enable_images,
                enable_video_generation=req.enable_video,
                enable_audio_generation=req.enable_audio,
            )

            llm_config = LLMConfig(
                provider=req.llm_provider,
                model=req.llm_model,
                api_key=api_key,
            )
            llm_client = LLMClient(llm_config)

            state = ProjectState(config=config)
            director = DirectorAgent(state, llm_client=llm_client)

            script = director.produce_film(
                prompt=req.prompt,
                title=req.title,
                genre=req.genre,
                target_duration=req.duration,
            )

            report = director.get_production_report()
            script_path = config.output_dir / "script.json"
            script_data = (
                json.loads(script_path.read_text()) if script_path.exists() else script.to_dict()
            )

            return {
                "success": True,
                "script": script_data,
                "report": report,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/script")
async def generate_script(req: ScriptRequest):
    try:
        from director_gpt.agents.screenwriter import ScreenwriterAgent

        api_key = req.llm_api_key or os.getenv("GEMINI_API_KEY")

        llm_config = LLMConfig(
            provider=req.llm_provider,
            model=req.llm_model,
            api_key=api_key,
        )
        llm_client = LLMClient(llm_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = ProjectConfig(
                project_name="script_gen",
                output_dir=Path(tmpdir),
            )
            state = ProjectState(config=config)
            screenwriter = ScreenwriterAgent("Screenwriter", state, llm_client=llm_client)

            result = screenwriter.process(
                {
                    "prompt": req.prompt,
                    "target_duration": req.duration,
                    "genre": req.genre,
                }
            )

            return {
                "success": True,
                "script": result,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
