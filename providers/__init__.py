import os
from typing import Optional

from bot import database


class Settings:
    """Runtime configuration for providers."""

    gemini_proxy: Optional[str] = os.getenv("GEMINI_PROXY")

    @classmethod
    async def reload(cls) -> None:
        cls.gemini_proxy = await database.get_config(
            "GEMINI_PROXY", os.getenv("GEMINI_PROXY")
        )


from .registry import ProviderRegistry  # noqa: E402

__all__ = ["ProviderRegistry", "Settings"]
