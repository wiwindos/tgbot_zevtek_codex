from __future__ import annotations

"""Gemini provider using google-generativeai SDK."""

import asyncio
import os
from typing import Any, Sequence

import google.generativeai as genai

from .base import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini LLM via GenAISDK."""

    name = "gemini"
    supports_files = True

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        model = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")
        self.model = model.replace("models/", "")
        self._configure()

    def _configure(self) -> None:
        try:
            genai.configure(api_key=self.api_key)
        except TypeError:
            genai.configure(api_key=self.api_key)
        self._client = genai.GenerativeModel(self.model)

    async def list_models(self) -> Sequence[str]:
        models = []
        for m in genai.list_models():
            methods = getattr(m, "supported_generation_methods", [])
            if "generateContent" in methods:
                models.append(m.name)
        return models

    async def generate(
        self,
        prompt: str,
        context: Sequence[tuple[str, str]] | None = None,
        file_bytes: bytes | None = None,
    ) -> str:
        def run() -> str:
            messages: list[dict[str, Any]] = []
            if context:
                for role, text in context:
                    messages.append({"role": role, "parts": [text]})
            if file_bytes is not None:
                messages.append(
                    {
                        "role": "user",
                        "parts": [prompt, file_bytes],
                    }
                )
            else:
                messages.append({"role": "user", "parts": [prompt]})
            resp = self._client.generate_content(messages)
            return str(getattr(resp, "text", ""))

        return await asyncio.to_thread(run)
