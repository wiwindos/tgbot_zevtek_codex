from __future__ import annotations

"""Gemini provider using google-generativeai SDK."""

import asyncio
import os
from typing import Any, Sequence

import google.generativeai as genai
import httpx

from bot import database

from .base import BaseProvider


class ProxyError(Exception):
    """Raised when proxy check fails."""


class GeminiProvider(BaseProvider):
    """Google Gemini LLM via GenAISDK."""

    name = "gemini"
    supports_files = True

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("DEFAULT_MODEL", "gemini-pro")
        self._proxy_url = os.getenv("GEMINI_PROXY")
        self._configure()

    def _configure(self) -> None:
        try:
            genai.configure(api_key=self.api_key, proxy=self._proxy_url)
        except TypeError:
            genai.configure(api_key=self.api_key)
        self._client = genai.GenerativeModel(self.model)

    async def reload_settings(self) -> None:
        self._proxy_url = await database.get_config(
            "GEMINI_PROXY", os.getenv("GEMINI_PROXY")
        )
        self._configure()

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

    async def check_proxy(self) -> None:
        if not self._proxy_url:
            raise ProxyError("Proxy not set")
        proxies = {"https": self._proxy_url}
        try:
            async with httpx.AsyncClient(proxies=proxies, timeout=5) as client:
                resp = await client.head("https://www.google.com/generate_204")
            if resp.status_code >= 400:
                raise ProxyError("Bad status")
        except httpx.HTTPError as exc:
            raise ProxyError(str(exc)) from exc
