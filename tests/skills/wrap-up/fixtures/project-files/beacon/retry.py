"""Retry budgeting for beacon's upload path."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class RetryBudget:
    """A retry allowance measured in elapsed wall-clock time, not attempts.

    An upload may retry as often as it likes while `remaining()` is positive.
    The budget starts when the first attempt is made and is never extended,
    so a slow endpoint cannot keep a sync alive indefinitely.
    """

    total_seconds: float
    _started_at: float | None = None

    def start(self) -> None:
        if self._started_at is None:
            self._started_at = time.monotonic()

    def remaining(self) -> float:
        if self._started_at is None:
            return self.total_seconds
        spent = time.monotonic() - self._started_at
        return max(0.0, self.total_seconds - spent)

    def exhausted(self) -> bool:
        return self.remaining() <= 0.0
