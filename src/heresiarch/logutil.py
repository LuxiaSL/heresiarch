"""Rate-limited warning logs for swallowed-exception hot paths.

Sim-critical failure sites (live recording, autosave analytics, the
training-data tap) deliberately swallow exceptions — a broken side
channel must never kill a run. But silent swallowing also hides real
data loss. :class:`RateLimitedLogger` makes those sites visible
without flooding hot loops: at most one warning per key per interval,
with a count of what was suppressed appended to the next emit.
"""

from __future__ import annotations

import logging
import time
from typing import Callable


class RateLimitedLogger:
    """Per-key rate limiter for warning logs.

    Thread-compat note: worst case under races is an extra or a lost
    suppression count — acceptable for diagnostics, so no lock.
    """

    def __init__(
        self,
        min_interval_s: float = 30.0,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._min_interval_s = min_interval_s
        self._clock = clock
        self._last_emit: dict[str, float] = {}
        self._suppressed: dict[str, int] = {}

    def warning(
        self,
        logger: logging.Logger,
        key: str,
        msg: str,
        *args: object,
    ) -> bool:
        """Log ``msg % args`` at WARNING unless ``key`` fired recently.

        Returns True when the record was emitted, False when it was
        suppressed. Suppressed calls are counted per key and the count
        is appended to the next emitted record.
        """
        now = self._clock()
        last = self._last_emit.get(key)
        if last is not None and (now - last) < self._min_interval_s:
            self._suppressed[key] = self._suppressed.get(key, 0) + 1
            return False
        suppressed = self._suppressed.pop(key, 0)
        if suppressed:
            msg = (
                f"{msg} [{suppressed} similar warning(s) suppressed in "
                f"the last {self._min_interval_s:.0f}s]"
            )
        logger.warning(msg, *args)
        self._last_emit[key] = now
        return True
