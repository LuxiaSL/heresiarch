"""RateLimitedLogger: emit/suppress windows and suppression counts."""

import logging

from heresiarch.logutil import RateLimitedLogger

logger = logging.getLogger("test.logutil")


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class TestRateLimitedLogger:
    def test_first_call_emits(self, caplog):
        rl = RateLimitedLogger(30.0, clock=_FakeClock())
        with caplog.at_level(logging.WARNING, "test.logutil"):
            assert rl.warning(logger, "k", "boom %s", 1) is True
        assert "boom 1" in caplog.text

    def test_within_interval_suppresses(self, caplog):
        clock = _FakeClock()
        rl = RateLimitedLogger(30.0, clock=clock)
        with caplog.at_level(logging.WARNING, "test.logutil"):
            assert rl.warning(logger, "k", "boom") is True
            clock.now = 29.9
            assert rl.warning(logger, "k", "boom") is False
        assert caplog.text.count("boom") == 1

    def test_after_interval_emits_with_suppressed_count(self, caplog):
        clock = _FakeClock()
        rl = RateLimitedLogger(30.0, clock=clock)
        with caplog.at_level(logging.WARNING, "test.logutil"):
            rl.warning(logger, "k", "boom")
            clock.now = 10.0
            rl.warning(logger, "k", "boom")
            rl.warning(logger, "k", "boom")
            clock.now = 31.0
            assert rl.warning(logger, "k", "boom") is True
        assert "2 similar warning(s) suppressed" in caplog.text

    def test_keys_are_independent(self, caplog):
        clock = _FakeClock()
        rl = RateLimitedLogger(30.0, clock=clock)
        with caplog.at_level(logging.WARNING, "test.logutil"):
            assert rl.warning(logger, "a", "alpha") is True
            assert rl.warning(logger, "b", "beta") is True
        assert "alpha" in caplog.text and "beta" in caplog.text

    def test_suppression_counter_resets_after_emit(self, caplog):
        clock = _FakeClock()
        rl = RateLimitedLogger(30.0, clock=clock)
        with caplog.at_level(logging.WARNING, "test.logutil"):
            rl.warning(logger, "k", "boom")
            clock.now = 5.0
            rl.warning(logger, "k", "boom")   # suppressed (1)
            clock.now = 31.0
            rl.warning(logger, "k", "boom")   # emits with count
            clock.now = 62.0
            rl.warning(logger, "k", "boom")   # emits WITHOUT stale count
        emits = [r for r in caplog.records if "boom" in r.getMessage()]
        assert len(emits) == 3
        assert "suppressed" not in emits[-1].getMessage()
