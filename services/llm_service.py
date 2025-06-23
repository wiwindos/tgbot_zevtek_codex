"""High level helpers for LLM operations."""

from __future__ import annotations

import os
from typing import cast

from bot import database
from providers import ProviderRegistry
from services import user_service
from services.context import ContextBuffer

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
    file_bytes: bytes | None = None,
    file_path: str | None = None,
    mime: str | None = None,
) -> str:
    registry = get_registry()
    if model is None:
        selected = _buffer.get_model(chat_id) if _buffer else None
        model = selected or os.getenv("DEFAULT_MODEL", "gemini-pro")
    model_str = cast(str, model)
    provider = registry.get(model_str.split("-")[0])
    user = await user_service.get_or_create_user(chat_id, str(chat_id))
    req_id = await database.log_request(user["id"], prompt, model_str)
    if file_path:
        await database.log_file(req_id, file_path, mime or "")
    text = await provider.generate(prompt, context=None, file_bytes=file_bytes)
    await database.log_response(req_id, text)
    return text
