"""Day 19: remember which GitHub deliveries we already processed.

GitHub gives every delivery a unique ID in the X-GitHub-Delivery header.
If we see the same ID again (redelivery, retry, network duplicate) we skip it.

This version keeps IDs in memory: perfect for one container and for learning.
With 2+ replicas you would use a shared store (Redis SET with NX + EX, or a DB unique key).
"""

import threading
import time
from collections import OrderedDict
from collections.abc import Callable


class DeliveryDeduper:
    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 10000, clock: Callable[[], float] = time.monotonic):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._clock = clock  # injectable so tests can "move time" without waiting
        self._seen: OrderedDict[str, float] = OrderedDict()  # delivery_id -> time processed
        self._lock = threading.Lock()

    def _forget_expired(self, now: float) -> None:
        while self._seen:
            oldest_id, seen_at = next(iter(self._seen.items()))
            if now - seen_at < self.ttl_seconds:
                break
            self._seen.pop(oldest_id)

    def already_processed(self, delivery_id: str) -> bool:
        """True if this delivery ID was processed within the TTL."""
        if not delivery_id:
            return False  # no ID = cannot dedupe; process it
        with self._lock:
            self._forget_expired(self._clock())
            return delivery_id in self._seen

    def mark_processed(self, delivery_id: str) -> None:
        """Call ONLY after processing succeeded, so a failed event can be redelivered and retried."""
        if not delivery_id:
            return
        with self._lock:
            now = self._clock()
            self._forget_expired(now)
            self._seen[delivery_id] = now
            self._seen.move_to_end(delivery_id)
            while len(self._seen) > self.max_entries:
                self._seen.popitem(last=False)  # drop the oldest

    def __len__(self) -> int:
        return len(self._seen)
