from __future__ import annotations

"""Gemini provider using google-generativeai SDK."""

import asyncio
import base64
import io
import os
from typing import Any, Sequence

import google.generativeai as genai
import pdfplumber

from services.file_service import FileKind, FilePayload

from .base import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini LLM via GenAISDK."""

    name = "gemini"
    supports_files = True
    supports_image = True
    supports_audio = True
    supports_text = True

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        model = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")
        self.model = model.replace("models/", "")
        self._configure()

    def set_model(self, name: str) -> None:
        self.model = name.replace("models/", "")
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
        file: FilePayload | None = None,
    ) -> str:
        def run() -> str:
            messages: list[dict[str, Any]] = []
            if context:
                for role, text in context:
                    messages.append({"role": role, "parts": [text]})
            if file is not None:
                if file.kind in {FileKind.IMAGE, FileKind.AUDIO}:
                    media_part = {
                        "mime_type": file.mime,
                        "data": base64.b64encode(file.data).decode(),
                    }
                    messages.append(
                        {
                            "role": "user",
                            "parts": [prompt, media_part],
                        }
                    )
                else:
                    if file.mime == "application/pdf":
                        text = ""
                        with pdfplumber.open(io.BytesIO(file.data)) as pdf:
                            for page in pdf.pages:
                                text += page.extract_text() or ""
                                if len(text) > 3000:
                                    break
                    else:
                        text = file.data.decode(errors="ignore")
                    snippet = text[:3000]
                    text_part = f"{prompt}\n'''{snippet}'''"
                    messages.append({"role": "user", "parts": [text_part]})
            else:
                messages.append({"role": "user", "parts": [prompt]})
            resp = self._client.generate_content(messages, stream=False)
            return str(getattr(resp, "text", ""))

        return await asyncio.to_thread(run)
