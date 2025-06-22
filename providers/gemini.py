"""Gemini provider using Google Vertex AI.

See https://cloud.google.com/vertex-ai/docs/generative-ai
"""

from __future__ import annotations

import os
from typing import Sequence

from google.cloud.aiplatform.gapic import PredictionServiceAsyncClient

from .base import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini LLM via Vertex AI."""

    name = "gemini"
    supports_files = True

    def __init__(self) -> None:
        project = os.getenv("GEMINI_PROJECT", "")
        location = os.getenv("GEMINI_LOCATION", "")
        self.api_key = os.getenv("GEMINI_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-pro")
        self._client = PredictionServiceAsyncClient(
            client_options={
                "api_endpoint": f"{location}-aiplatform.googleapis.com",
            },
        )
        self._parent = (
            f"projects/{project}/locations/{location}/publishers/google/"
            f"models/{self.model}"
        )

    async def list_models(self) -> Sequence[str]:
        # In real implementation we would call modelsClient.list_models
        return [self.model]

    async def generate(
        self,
        prompt: str,
        context: Sequence[tuple[str, str]] | None = None,
        file_bytes: bytes | None = None,
    ) -> str:
        # Real payload structure simplified for demo
        if file_bytes is not None:
            instances = [{"prompt": prompt, "file": file_bytes}]
        else:
            instances = [{"prompt": prompt}]
        response = await self._client.predict(
            endpoint=self._parent, instances=instances, parameters={}
        )
        return response.predictions[0].get("content", "")
