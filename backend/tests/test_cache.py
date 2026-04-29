import unittest
from threading import Barrier, Lock, Thread
from time import monotonic, sleep

from backend.app.cache import TtlCache


class TtlCacheTests(unittest.TestCase):
    def test_get_or_set_reuses_fresh_value(self) -> None:
        calls = 0
        cache = TtlCache(ttl_seconds=30)

        def factory() -> list[int]:
            nonlocal calls
            calls += 1
            return [calls]

        self.assertEqual(cache.get_or_set("items", factory), [1])
        self.assertEqual(cache.get_or_set("items", factory), [1])
        self.assertEqual(calls, 1)

    def test_get_or_set_can_serve_stale_value_when_refresh_fails(self) -> None:
        cache = TtlCache(ttl_seconds=-1, stale_seconds=30)
        cache.get_or_set("items", lambda: ["cached"])

        def failing_factory() -> list[str]:
            raise RuntimeError("backend unavailable")

        self.assertEqual(cache.get_or_set("items", failing_factory), ["cached"])

    def test_get_or_set_raises_without_stale_value(self) -> None:
        cache = TtlCache(ttl_seconds=-1, stale_seconds=0)

        with self.assertRaises(RuntimeError):
            cache.get_or_set("items", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    def test_slow_refresh_for_one_key_does_not_block_other_keys(self) -> None:
        cache = TtlCache(ttl_seconds=30)
        barrier = Barrier(2)
        results: list[str] = []
        lock = Lock()

        def load(key: str) -> None:
            barrier.wait()
            value = cache.get_or_set(key, lambda: (sleep(0.2), key)[1])
            with lock:
                results.append(value)

        started_at = monotonic()
        threads = [Thread(target=load, args=(key,)) for key in ("profiles", "items")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertLess(monotonic() - started_at, 0.35)
        self.assertCountEqual(results, ["profiles", "items"])

    def test_concurrent_refresh_for_same_key_uses_one_factory_call(self) -> None:
        cache = TtlCache(ttl_seconds=30)
        barrier = Barrier(3)
        calls = 0
        results: list[list[int]] = []
        lock = Lock()

        def factory() -> list[int]:
            nonlocal calls
            with lock:
                calls += 1
            sleep(0.1)
            return [calls]

        def load() -> None:
            barrier.wait()
            value = cache.get_or_set("profiles", factory)
            with lock:
                results.append(value)

        threads = [Thread(target=load) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(calls, 1)
        self.assertEqual(results, [[1], [1], [1]])

    def test_max_entries_evicts_oldest_cached_values(self) -> None:
        cache = TtlCache(ttl_seconds=30, max_entries=2)
        calls = 0

        def factory() -> int:
            nonlocal calls
            calls += 1
            return calls

        self.assertEqual(cache.get_or_set("first", factory), 1)
        self.assertEqual(cache.get_or_set("second", factory), 2)
        self.assertEqual(cache.get_or_set("third", factory), 3)
        self.assertEqual(cache.get_or_set("second", factory), 2)
        self.assertEqual(cache.get_or_set("first", factory), 4)

    def test_max_entries_prunes_expired_stale_values_first(self) -> None:
        cache = TtlCache(ttl_seconds=-1, stale_seconds=-1, max_entries=2)

        self.assertEqual(cache.get_or_set("expired", lambda: "old"), "old")
        self.assertEqual(cache.get_or_set("fresh-a", lambda: "a"), "a")
        self.assertEqual(cache.get_or_set("fresh-b", lambda: "b"), "b")

        with self.assertRaises(RuntimeError):
            cache.get_or_set("expired", lambda: (_ for _ in ()).throw(RuntimeError("expired")))

    def test_max_entries_rejects_invalid_limits(self) -> None:
        with self.assertRaises(ValueError):
            TtlCache(ttl_seconds=30, max_entries=0)


if __name__ == "__main__":
    unittest.main()
