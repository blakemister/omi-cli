from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from omi_cli.dates import parse_window

UTC = timezone.utc


def test_none_returns_none():
    assert parse_window(None) is None
    assert parse_window("") is None


def test_today_and_yesterday():
    today = parse_window("today")
    yesterday = parse_window("yesterday")
    assert today and yesterday
    assert today.hour == 0 and yesterday.hour == 0
    assert today.date() - yesterday.date() == timedelta(days=1)


@pytest.mark.parametrize("value,hours", [("7d", 7 * 24), ("2w", 14 * 24), ("3h", 3), ("1m", 30 * 24)])
def test_relative_windows(value, hours):
    now = datetime.now(UTC)
    parsed = parse_window(value)
    assert parsed is not None
    delta = (now - parsed).total_seconds() / 3600
    assert abs(delta - hours) < 1


def test_iso_roundtrip():
    iso = "2026-04-14T12:00:00+00:00"
    assert parse_window(iso).isoformat() == iso


def test_invalid_raises():
    with pytest.raises(ValueError):
        parse_window("not-a-date")
