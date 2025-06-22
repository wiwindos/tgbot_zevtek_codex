from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence


class BaseProvider(ABC):
    """Abstract provider interface."""

    name: str
    supports_files: bool = False

    @abstractmethod
    async def list_models(self) -> Sequence[str]:
        """Return available model names."""

    @abstractmethod
    async def generate(
        self, prompt: str, context: Sequence[tuple[str, str]] | None = None
    ) -> str:
        """Generate text from LLM."""
