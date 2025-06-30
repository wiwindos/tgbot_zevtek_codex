"""Helpers for uploaded file validation and MIME detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from mimetypes import guess_type

try:
    import magic
except ImportError:  # pragma: no cover - fallback when libmagic is absent
    magic = None

MAX_FILE_SIZE = 512_000  # 512 kB
ALLOWED_IMAGE = {"image/png", "image/jpeg"}
ALLOWED_AUDIO = {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/ogg"}
ALLOWED_TEXT = {"text/plain", "application/pdf"}


class FileTooLarge(Exception):
    """Raised when uploaded file exceeds ``MAX_FILE_SIZE``."""


class UnsupportedMime(Exception):
    """Raised when file MIME type is not supported."""


class FileKind(Enum):
    """High level file categories."""

    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"
    UNSUPPORTED = "unsupported"


@dataclass
class FilePayload:
    """Container for validated file bytes."""

    data: bytes
    mime: str
    kind: FileKind


def detect_mime(data: bytes, filename: str | None = None) -> FilePayload:
    """Return file description after size and type checks."""
    if len(data) > MAX_FILE_SIZE:
        raise FileTooLarge()
    mime = None
    if filename:
        mime = guess_type(filename)[0]
    if (not mime or mime == "application/octet-stream") and magic:
        try:
            mime = magic.from_buffer(data, mime=True)
        except Exception:  # pragma: no cover - libmagic misconfigured
            mime = None
    mime = mime or "application/octet-stream"
    if mime in ALLOWED_IMAGE:
        kind = FileKind.IMAGE
    elif mime in ALLOWED_AUDIO:
        kind = FileKind.AUDIO
    elif mime in ALLOWED_TEXT:
        kind = FileKind.TEXT
    else:
        raise UnsupportedMime(mime)
    return FilePayload(data=data, mime=mime, kind=kind)
