"""Retry helper with exponential backoff for external service calls."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger("sde.retry")

T = TypeVar("T")


def with_retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    label: str = "operation",
) -> T:
    """Run fn up to `attempts` times with exponential backoff."""
    last: BaseException | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except exceptions as exc:
            last = exc
            if attempt >= attempts - 1:
                break
            delay = min(base_delay * (2**attempt), max_delay)
            logger.warning(
                "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                label,
                attempt + 1,
                attempts,
                exc,
                delay,
            )
            time.sleep(delay)
    assert last is not None
    raise last
