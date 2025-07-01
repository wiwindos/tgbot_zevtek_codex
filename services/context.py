"""Per-chat message history buffer.

Stores recent user and bot messages to preserve conversation context.
Messages are kept in insertion order and trimmed to ``max_messages`` entries.
"""

from collections import deque
from typing import Deque, Dict, List, Tuple


class ContextBuffer:
    """In-memory circular buffer for chat messages."""

    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max_messages
        self._data: Dict[int, Deque[Tuple[str, str]]] = {}
        self.user_provider: Dict[int, str] = {}
        self.user_models: Dict[int, Dict[str, str]] = {}
        self.warned: Dict[int, bool] = {}

    def add(self, chat_id: int, role: str, text: str) -> None:
        queue = self._data.setdefault(chat_id, deque(maxlen=self.max_messages))
        queue.append((role, text))

    def get(self, chat_id: int) -> List[Tuple[str, str]]:
        return list(self._data.get(chat_id, deque()))

    def total_chars(self, chat_id: int) -> int:
        return sum(len(t) for _, t in self._data.get(chat_id, []))

    def clear(self, chat_id: int) -> None:
        self._data.pop(chat_id, None)
        self.warned.pop(chat_id, None)

    def set_provider(self, chat_id: int, provider: str) -> None:
        self.user_provider[chat_id] = provider

    def get_provider(self, chat_id: int) -> str | None:
        return self.user_provider.get(chat_id)

    def set_model(self, chat_id: int, model: str) -> None:
        provider = model.split("-")[0]
        models = self.user_models.setdefault(chat_id, {})
        models[provider] = model
        self.user_provider.setdefault(chat_id, provider)

    def get_model(self, chat_id: int) -> str | None:
        provider = self.get_provider(chat_id)
        if provider is None:
            return None
        return self.user_models.get(chat_id, {}).get(provider)
