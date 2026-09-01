"""LLM client abstraction supporting multiple providers."""

from typing import Optional
import os

from director_gpt.utils.config import LLMConfig


class LLMClient:
    """Unified LLM client for OpenAI, Gemini, etc."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = config.provider.lower()
        self.model = config.model
        self.api_key = config.api_key or os.getenv(f"{self.provider.upper()}_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        return self._client

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        client = self._get_client()

        if self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            return response.choices[0].message.content or ""

        elif self.provider == "gemini":
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                },
            )
            return response.text or ""

        raise ValueError(f"Unsupported provider: {self.provider}")

    def chat(self, messages: list[dict], system_prompt: Optional[str] = None) -> str:
        client = self._get_client()

        if self.provider == "openai":
            openai_messages = []
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            openai_messages.extend(messages)

            response = client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            return response.choices[0].message.content or ""

        elif self.provider == "gemini":
            history = []
            for msg in messages:
                role = "user" if msg.get("role") == "user" else "model"
                history.append({"role": role, "parts": [msg.get("content", "")]})

            chat = client.start_chat(history=history)
            last_msg = messages[-1].get("content", "") if messages else ""
            if system_prompt:
                last_msg = f"{system_prompt}\n\n{last_msg}"

            response = chat.send_message(
                last_msg,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                },
            )
            return response.text or ""

        raise ValueError(f"Unsupported provider: {self.provider}")
