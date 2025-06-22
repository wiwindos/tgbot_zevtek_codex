"""Dipseek provider via HTTPX.

See https://dipseek.ai/docs
"""

from __future__ import annotations

import os
from typing import Sequence

import httpx

from .base import BaseProvider


class DipseekProvider(BaseProvider):
    """Dipseek chat models."""

    name = "dipseek"

    def __init__(self) -> None:
        self.endpoint = os.getenv("DIPSEEK_ENDPOINT", "https://dipseek.ai")
        self.api_key = os.getenv("DIPSEEK_API_KEY", "")
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
            raise NotImplementedError("Files not supported")
        payload = {"messages": [{"role": "user", "content": prompt}]}
        resp = await self._client.post(
            "/v1/chat/completions",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
