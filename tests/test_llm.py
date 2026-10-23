"""Tests for the LLM client."""

from unittest.mock import MagicMock, patch

import pytest

from director_gpt.llm import LLMClient
from director_gpt.utils.config import LLMConfig


def make_llm_config(provider: str = "openai", model: str = "gpt-4") -> LLMConfig:
    return LLMConfig(provider=provider, model=model, api_key="test-key")


def test_llm_client_initialization():
    """LLMClient should initialize with config values."""
    config = make_llm_config()
    client = LLMClient(config)
    assert client.provider == "openai"
    assert client.model == "gpt-4"
    assert client.api_key == "test-key"


def test_llm_client_openai_generate():
    """LLMClient should generate text using OpenAI provider."""
    pytest.importorskip("openai")
    config = make_llm_config(provider="openai")
    client = LLMClient(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello from OpenAI"

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_openai):
        result = client.generate("Hello", system_prompt="Be helpful")
        assert result == "Hello from OpenAI"


def test_llm_client_gemini_generate():
    """LLMClient should generate text using Gemini provider."""
    config = make_llm_config(provider="gemini", model="gemini-2.0-flash")
    client = LLMClient(config)

    mock_response = MagicMock()
    mock_response.text = "Hello from Gemini"

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch("google.generativeai.GenerativeModel", return_value=mock_model):
        result = client.generate("Hello", system_prompt="Be helpful")
        assert result == "Hello from Gemini"


def test_llm_client_unsupported_provider():
    """LLMClient should raise ValueError for unsupported providers."""
    config = LLMConfig(provider="unsupported", model="test", api_key="key")
    client = LLMClient(config)
    try:
        client._get_client()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "unsupported" in str(e).lower()


def test_llm_client_generate_with_retries():
    """LLMClient should retry on transient errors."""
    config = make_llm_config()
    client = LLMClient(config)
    client._max_retries = 2
    client._retry_delay = 0.01

    call_count = 0

    def flaky_fn() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("Transient error")
        return "Success"

    result = client._with_retries(flaky_fn)
    assert result == "Success"
    assert call_count == 2


def test_llm_client_generate_all_retries_fail():
    """LLMClient should raise after exhausting retries."""
    config = make_llm_config()
    client = LLMClient(config)
    client._max_retries = 2
    client._retry_delay = 0.01

    def always_fails() -> str:
        raise RuntimeError("Always fails")

    try:
        client._with_retries(always_fails)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "Always fails" in str(e)


def test_llm_client_chat_openai():
    """LLMClient chat method should work with OpenAI."""
    pytest.importorskip("openai")
    config = make_llm_config(provider="openai")
    client = LLMClient(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Chat response"

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_openai):
        result = client.chat(
            [{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful",
        )
        assert result == "Chat response"


def test_llm_client_chat_gemini():
    """LLMClient chat method should work with Gemini."""
    config = make_llm_config(provider="gemini", model="gemini-2.0-flash")
    client = LLMClient(config)

    mock_response = MagicMock()
    mock_response.text = "Chat response from Gemini"

    mock_chat = MagicMock()
    mock_chat.send_message.return_value = mock_response

    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat

    with patch("google.generativeai.GenerativeModel", return_value=mock_model):
        result = client.chat(
            [{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful",
        )
        assert result == "Chat response from Gemini"
