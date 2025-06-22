"""High level helpers for LLM operations."""

from __future__ import annotations

from bot import database
from providers import ProviderRegistry
from services import user_service

_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


async def generate_reply(
    chat_id: int,
    prompt: str,
    model: str,
    *,
    file_bytes: bytes | None = None,
    file_path: str | None = None,
    mime: str | None = None,
) -> str:
    registry = get_registry()
    provider = registry.get(model.split("-", 1)[0])
    user = await user_service.get_or_create_user(chat_id, str(chat_id))
    req_id = await database.log_request(user["id"], prompt, model)
    if file_path:
        await database.log_file(req_id, file_path, mime or "")
    text = await provider.generate(prompt, context=None, file_bytes=file_bytes)
    await database.log_response(req_id, text)
    return text
