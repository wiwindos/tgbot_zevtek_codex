"""High level helpers for LLM operations."""

from __future__ import annotations

import os
from typing import cast

from bot import database
from providers import ProviderRegistry
from services import user_service
from services.context import ContextBuffer
from services.file_service import FilePayload
from services.llm import safe_generate

_registry: ProviderRegistry | None = None
_buffer: ContextBuffer | None = None


def get_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def set_context_buffer(buffer: ContextBuffer) -> None:
    global _buffer
    _buffer = buffer


async def generate_reply(
    chat_id: int,
    prompt: str,
    model: str | None = None,
    *,
    file: FilePayload | None = None,
    file_path: str | None = None,
    mime: str | None = None,
) -> str:
    registry = get_registry()
    if model is None:
        selected_model = _buffer.get_model(chat_id) if _buffer else None
        model = selected_model or os.getenv(
            "DEFAULT_MODEL",
            "gemini-2.0-flash",
        )
    model_str = cast(str, model)
    provider_name = model_str.split("-")[0]
    provider = registry.get(provider_name, model_str)
    if _buffer:
        _buffer.set_provider(chat_id, provider_name)
        _buffer.set_model(chat_id, model_str)
    user = await user_service.get_or_create_user(chat_id, str(chat_id))
    req_id = await database.log_request(user["id"], prompt, model_str)
    if file_path:
        await database.log_file(req_id, file_path, mime or "")
    history = _buffer.get(chat_id) if _buffer else []
    text = await safe_generate(
        provider,
        prompt,
        context=history,
        file=file,
    )
    await database.log_response(req_id, text)
    return text
