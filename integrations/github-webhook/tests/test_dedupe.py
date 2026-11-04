"""Day 19: duplicate-delivery memory (unit tests, no web server)."""

from app.dedupe import DeliveryDeduper


class FakeClock:
    """A clock we can move forward by hand, so TTL tests take 0 seconds."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_new_id_is_not_a_duplicate():
    d = DeliveryDeduper()
    assert d.already_processed("abc") is False


def test_id_is_a_duplicate_after_it_was_processed():
    d = DeliveryDeduper()
    d.mark_processed("abc")
    assert d.already_processed("abc") is True
    assert d.already_processed("xyz") is False


def test_id_is_forgotten_after_ttl():
    clock = FakeClock()
    d = DeliveryDeduper(ttl_seconds=60, clock=clock)
    d.mark_processed("abc")
    clock.now += 59
    assert d.already_processed("abc") is True
    clock.now += 2  # 61 s later
    assert d.already_processed("abc") is False


def test_oldest_ids_are_dropped_when_full():
    d = DeliveryDeduper(max_entries=100)
    for i in range(101):
        d.mark_processed(f"id-{i}")
    assert len(d) == 100
    assert d.already_processed("id-0") is False  # the oldest was dropped
    assert d.already_processed("id-100") is True


def test_empty_id_is_never_a_duplicate():
    d = DeliveryDeduper()
    d.mark_processed("")
    assert d.already_processed("") is False
