from __future__ import annotations

from collections.abc import Callable, Hashable
from threading import Event, RLock
from time import monotonic
from typing import TypeVar


T = TypeVar("T")


class TtlCache:
    def __init__(self, ttl_seconds: float, *, stale_seconds: float = 0) -> None:
        self.ttl_seconds = ttl_seconds
        self.stale_seconds = stale_seconds
        self._lock = RLock()
        self._items: dict[Hashable, tuple[float, float, object]] = {}
        self._refreshing: dict[Hashable, Event] = {}

    def get_or_set(self, key: Hashable, factory: Callable[[], T]) -> T:
        while True:
            with self._lock:
                cached = self._items.get(key)
                if cached and monotonic() < cached[0]:
                    return cached[2]  # type: ignore[return-value]

                refresh_done = self._refreshing.get(key)
                if refresh_done is None:
                    refresh_done = Event()
                    self._refreshing[key] = refresh_done
                    break

            refresh_done.wait()

        try:
            value = factory()
        except Exception:
            with self._lock:
                cached = self._items.get(key)
                self._refreshing.pop(key, None)
                refresh_done.set()
                if cached and monotonic() < cached[1]:
                    return cached[2]  # type: ignore[return-value]
            raise

        self._store_value(key, value, refresh_done)
        return value

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def _store_value(self, key: Hashable, value: object, refresh_done: Event) -> None:
        now = monotonic()
        expires_at = now + self.ttl_seconds
        stale_until = expires_at + self.stale_seconds
        with self._lock:
            self._items[key] = (expires_at, stale_until, value)
            self._refreshing.pop(key, None)
            refresh_done.set()
