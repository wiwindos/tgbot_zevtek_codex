from __future__ import annotations

"""Utilities for safe provider calls."""

from time import perf_counter

from providers.base import BaseProvider


class ProviderError(Exception):
    """Wrap provider exceptions with meta info."""

    def __init__(
        self, provider: str, model: str | None, exc: Exception, elapsed: float
    ) -> None:
        super().__init__(str(exc))
        self.provider = provider
        self.model = model
        self.orig_exc = exc
        self.elapsed = elapsed


async def safe_generate(
    provider: BaseProvider,
    prompt: str,
    *,
    context: list[tuple[str, str]] | None = None,
    file=None,
):
    """Call provider.generate catching all errors."""
    start = perf_counter()
    try:
        return await provider.generate(prompt, context=context, file=file)
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(
            provider.name,
            getattr(provider, "model", None),
            exc,
            perf_counter() - start,
        )
