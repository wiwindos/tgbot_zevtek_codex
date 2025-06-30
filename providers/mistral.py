"""Mistral provider via HTTPX.

API docs: https://docs.mistral.ai/api/
"""

from __future__ import annotations

import os
from typing import Sequence

import httpx

from .base import BaseProvider


class MistralProvider(BaseProvider):
    """Mistral AI models over HTTP."""

    name = "mistral"

    def __init__(self) -> None:
        self.api_key = os.getenv("MISTRAL_API_KEY", "")
        self.base_url = os.getenv("MISTRAL_ENDPOINT", "https://api.mistral.ai")
        self.model = os.getenv("DEFAULT_MODEL", "mistral-small")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

    def set_model(self, name: str) -> None:
        self.model = name

    async def list_models(self) -> Sequence[str]:
        resp = await self._client.get("/v1/models")
        resp.raise_for_status()
        data = resp.json()
        return [m["id"] for m in data.get("data", [])]

    async def generate(
        self,
        prompt: str,
        context: Sequence[tuple[str, str]] | None = None,
        file_bytes: bytes | None = None,
    ) -> str:
        if file_bytes is not None:
            raise NotImplementedError("Files are not supported")
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = await self._client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
