"""Tests for retry helper."""
from __future__ import annotations

import pytest

from app.retry import with_retry


def test_succeeds_first_try():
    assert with_retry(lambda: 42, attempts=3) == 42


def test_retries_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    assert with_retry(flaky, attempts=3, base_delay=0.01) == "ok"
    assert calls["n"] == 3


def test_raises_after_exhausted_attempts():
    with pytest.raises(ValueError):
        with_retry(lambda: (_ for _ in ()).throw(ValueError("fail")), attempts=2, base_delay=0.01)
