"""Deepseek provider via HTTPX.

See https://deepseek.com/docs
"""

from __future__ import annotations

import os
from typing import Sequence

import httpx

from .base import BaseProvider


class DeepseekProvider(BaseProvider):
    """Deepseek chat models."""

    name = "deepseek"

    def __init__(self) -> None:
        self.endpoint = os.getenv(
            "DEEPSEEK_ENDPOINT",
            "https://api.deepseek.com",
        )
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self._client = httpx.AsyncClient(
            base_url=self.endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

    async def list_models(self) -> Sequence[str]:
        resp = await self._client.get("/v1/models")
        resp.raise_for_status()
        data = resp.json()
        return data.get("models", [])

    async def generate(
        self,
        prompt: str,
        context: Sequence[tuple[str, str]] | None = None,
        file_bytes: bytes | None = None,
    ) -> str:
        if file_bytes is not None:
            raise NotImplementedError("Files are not supported")
        payload = {"messages": [{"role": "user", "content": prompt}]}
        resp = await self._client.post(
            "/chat/completions",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
