"""Tests for utility functions."""

from director_gpt.utils import (
    clean_json_text,
    ensure_dir,
    extract_json_from_text,
    format_duration,
    get_api_key,
    parse_llm_json,
    safe_import,
    slugify,
)


def test_clean_json_text_with_json_fence():
    raw = '```json\n{"key": "value"}\n```'
    cleaned = clean_json_text(raw)
    assert cleaned == '{"key": "value"}'


def test_clean_json_text_with_generic_fence():
    raw = '```\n{"key": "value"}\n```'
    cleaned = clean_json_text(raw)
    assert cleaned == '{"key": "value"}'


def test_clean_json_text_plain():
    raw = '{"key": "value"}'
    cleaned = clean_json_text(raw)
    assert cleaned == '{"key": "value"}'


def test_clean_json_text_with_whitespace():
    raw = '  ```json\n{"key": "value"}\n```  '
    cleaned = clean_json_text(raw)
    assert cleaned == '{"key": "value"}'


def test_format_duration():
    assert format_duration(0) == "0:00:00"
    assert format_duration(60) == "1:00:00"
    assert format_duration(90.5) == "1:30:12"  # 0.5 * 24 = 12 frames


def test_safe_import_existing():
    import os

    mod, err = safe_import("os")
    assert mod is os
    assert err is None


def test_safe_import_missing():
    mod, err = safe_import("nonexistent_package_xyz")
    assert mod is None
    assert err is not None
    assert "nonexistent_package_xyz" in err


def test_extract_json_from_text_with_surrounding_text():
    text = 'Here is the result: {"a": 1, "b": [2, 3]} done.'
    result = extract_json_from_text(text)
    assert result == '{"a": 1, "b": [2, 3]}'


def test_extract_json_from_text_no_json():
    assert extract_json_from_text("no json here") is None


def test_parse_llm_json_with_fence():
    raw = '```json\n{"key": "value"}\n```'
    result = parse_llm_json(raw)
    assert result == {"key": "value"}


def test_parse_llm_json_with_embedded_text():
    raw = 'Sure! Here is the JSON: {"name": "test", "count": 3}'
    result = parse_llm_json(raw)
    assert result == {"name": "test", "count": 3}


def test_parse_llm_json_invalid():
    assert parse_llm_json("not json at all") is None


def test_slugify():
    assert slugify("Hello World!") == "hello-world"
    assert slugify("  Multiple   Spaces  ") == "multiple-spaces"
    assert slugify("Film: A Drama!") == "film-a-drama"


def test_ensure_dir(tmp_path):
    target = tmp_path / "sub" / "dir"
    result = ensure_dir(target)
    assert result.exists()
    assert result.is_dir()


def test_get_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert get_api_key("openai") == "sk-test"


def test_get_api_key_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_SECRET", raising=False)
    assert get_api_key("anthropic") is None