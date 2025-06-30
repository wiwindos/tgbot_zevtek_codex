from __future__ import annotations

import inspect
from typing import Dict, Sequence, Type, cast

from .base import BaseProvider
from .deepseek import DeepseekProvider  # noqa: F401
from .gemini import GeminiProvider  # noqa: F401
from .mistral import MistralProvider  # noqa: F401


class ProviderRegistry:
    """Discover and provide access to LLM providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}
        for cls in BaseProvider.__subclasses__():
            if inspect.isabstract(cls):
                continue
            concrete = cast(Type[BaseProvider], cls)
            instance = concrete()
            self._providers[concrete.name] = instance

    async def list_all(self) -> Sequence[str]:
        models: set[str] = set()
        for provider in self._providers.values():
            for model in await provider.list_models():
                models.add(model)
        return list(models)

    def get(self, name: str) -> BaseProvider:
        return self._providers[name]
