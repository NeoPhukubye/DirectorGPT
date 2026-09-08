"""Tests for utility functions."""

from director_gpt.utils import (
    clean_json_text,
    format_duration,
    safe_import,
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
