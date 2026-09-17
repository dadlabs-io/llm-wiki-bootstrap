"""The single network seam. Every remote call in beacon goes through send()."""

from __future__ import annotations

from collections.abc import Callable

Sender = Callable[[str, bytes], int]


def send(url: str, payload: bytes, sender: Sender) -> int:
    """Post payload to url through the injected sender and return its status.

    beacon never calls an HTTP library directly anywhere else: tests pass a
    sender that fails on demand, which is how the retry paths are exercised
    without a network or a sleep.
    """
    return sender(url, payload)
