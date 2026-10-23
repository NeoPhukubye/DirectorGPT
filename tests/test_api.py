"""Tests for the FastAPI backend."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app


def test_health_endpoint():
    """Health endpoint should return ok status."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_produce_request_validation():
    """ProduceRequest should validate duration and fps."""
    client = TestClient(app)

    # Test invalid duration
    response = client.post(
        "/api/produce",
        json={
            "prompt": "test",
            "duration": -1.0,
        },
    )
    assert response.status_code == 422

    # Test invalid fps
    response = client.post(
        "/api/produce",
        json={
            "prompt": "test",
            "fps": 0,
        },
    )
    assert response.status_code == 422


def test_script_request_validation():
    """ScriptRequest should validate duration."""
    client = TestClient(app)
    response = client.post(
        "/api/script",
        json={
            "prompt": "test",
            "duration": 0.0,
        },
    )
    assert response.status_code == 422


def test_parse_resolution_valid():
    """_parse_resolution should handle valid resolutions."""
    from api.main import _parse_resolution

    assert _parse_resolution("1920x1080") == (1920, 1080)
    assert _parse_resolution("1280x720") == (1280, 720)


def test_parse_resolution_invalid():
    """_parse_resolution should raise for invalid resolutions."""
    from fastapi import HTTPException

    from api.main import _parse_resolution

    try:
        _parse_resolution("invalid")
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 422


def test_produce_endpoint_success():
    """Produce endpoint should return success with script and report."""
    client = TestClient(app)

    mock_director = MagicMock()
    mock_script = MagicMock()
    mock_script.to_dict.return_value = {
        "title": "Test",
        "scenes": [],
        "characters": [],
    }
    mock_director.produce_film.return_value = mock_script
    mock_director.get_production_report.return_value = {
        "scenes": 1,
        "total_shots": 3,
        "characters": 2,
    }

    with patch("api.main.DirectorAgent", return_value=mock_director):
        response = client.post(
            "/api/produce",
            json={
                "prompt": "A test story",
                "title": "Test Film",
                "genre": "drama",
                "duration": 60.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "script" in data
        assert "report" in data


def test_script_endpoint_success():
    """Script endpoint should return success with script."""
    client = TestClient(app)

    mock_screenwriter = MagicMock()
    mock_screenwriter.process.return_value = {
        "characters": [{"name": "Test"}],
        "scenes": [{"scene_number": 1, "shots": []}],
    }

    with patch(
        "director_gpt.agents.screenwriter.ScreenwriterAgent", return_value=mock_screenwriter
    ):
        response = client.post(
            "/api/script",
            json={
                "prompt": "A test story",
                "genre": "drama",
                "duration": 60.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "script" in data
