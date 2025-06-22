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

    def add(self, chat_id: int, role: str, text: str) -> None:
        queue = self._data.setdefault(chat_id, deque(maxlen=self.max_messages))
        queue.append((role, text))

    def get(self, chat_id: int) -> List[Tuple[str, str]]:
        return list(self._data.get(chat_id, deque()))

    def clear(self, chat_id: int) -> None:
        self._data.pop(chat_id, None)
