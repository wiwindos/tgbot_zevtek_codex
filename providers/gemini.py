"""Gemini provider using Google Vertex AI.

See https://cloud.google.com/vertex-ai/docs/generative-ai
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Sequence

import httpx

from bot import database

from .base import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini LLM via Vertex AI."""

    name = "gemini"
    supports_files = True

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-pro")
        try:
            self._proxy_url = asyncio.run(database.get_setting("gemini_proxy"))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            self._proxy_url = loop.run_until_complete(
                database.get_setting("gemini_proxy")
            )
            loop.close()

    async def list_models(self) -> Sequence[str]:
        # In real implementation we would call modelsClient.list_models
        return [self.model]

    async def generate(
        self,
        prompt: str,
        context: Sequence[tuple[str, str]] | None = None,
        file_bytes: bytes | None = None,
    ) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        payload: dict[str, Any] = {"prompt": prompt}
        if file_bytes is not None:
            payload["file"] = file_bytes
        proxies = {"all://": self._proxy_url} if self._proxy_url else None
        async with httpx.AsyncClient(proxies=proxies) as client:
            resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("predictions", [{}])[0].get("content", "")
        return str(content)
